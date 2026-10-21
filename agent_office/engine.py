"""Guarded workflow runner and SQLite task/run persistence."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_TOOLS = {"utc_now", "read_project_file", "send_telegram", "github_create_issue", "github_open_pr"}
SIDE_EFFECT_TOOLS = {"send_telegram", "github_create_issue", "github_open_pr"}

class WorkflowValidationError(ValueError): pass
class ToolExecutionError(RuntimeError): pass

def validate_workflow(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) - {"name", "goal", "steps"}:
        raise WorkflowValidationError("workflow must contain only name, goal, and steps")
    name, goal, steps = value.get("name"), value.get("goal"), value.get("steps")
    if not isinstance(name, str) or not name.strip() or len(name) > 100: raise WorkflowValidationError("name must be 1-100 characters")
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 1000: raise WorkflowValidationError("goal must be 1-1000 characters")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 30: raise WorkflowValidationError("steps must contain 1-30 entries")
    clean, ids = [], set()
    for i, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) - {"id", "tool", "args"}: raise WorkflowValidationError(f"step {i} has an invalid shape")
        step_id, tool, args = step.get("id"), step.get("tool"), step.get("args", {})
        if not isinstance(step_id, str) or not step_id.strip() or len(step_id) > 60 or step_id in ids: raise WorkflowValidationError(f"step {i} has invalid or duplicate id")
        if tool not in ALLOWED_TOOLS: raise WorkflowValidationError(f"step {i} uses an unregistered tool")
        if not isinstance(args, dict) or len(args) > 20: raise WorkflowValidationError(f"step {i} args must be a small object")
        ids.add(step_id); clean.append({"id":step_id,"tool":tool,"args":args})
    return {"name":name.strip(),"goal":goal.strip(),"steps":clean}

def run_workflow(workflow: dict[str, Any], root: str | Path = ".") -> dict[str, Any]:
    wf = validate_workflow(workflow); results=[]; status="succeeded"
    for step in wf["steps"]:
        tool, args = step["tool"], step["args"]
        if tool in SIDE_EFFECT_TOOLS:
            results.append({"id":step["id"],"tool":tool,"status":"needs_approval","reason":"side-effect adapter is disabled until approval wiring exists"})
            status="needs_approval"; break
        if tool == "utc_now": result={"utc":datetime.now(timezone.utc).isoformat()}
        elif tool == "read_project_file":
            relative=args.get("path")
            if not isinstance(relative,str) or not relative or len(relative)>240: raise ToolExecutionError("path must be a relative file path")
            base=Path(root).resolve(); candidate=(base/relative).resolve()
            if candidate != base and base not in candidate.parents: raise ToolExecutionError("path escapes project root")
            if not candidate.is_file(): raise ToolExecutionError("file does not exist")
            if candidate.stat().st_size>100_000: raise ToolExecutionError("file exceeds 100 KB read limit")
            result={"path":str(candidate.relative_to(base)),"content":candidate.read_text(encoding="utf-8")}
        else: raise ToolExecutionError("tool has no executor")
        results.append({"id":step["id"],"tool":tool,"status":"succeeded","result":result})
    return {"name":wf["name"],"goal":wf["goal"],"status":status,"results":results}

class TaskStore:
    def __init__(self, path: str | Path = "agent_office/state.sqlite3"):
        self.path=str(path); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            db.execute("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, event TEXT NOT NULL, details TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(task_id) REFERENCES tasks(id))")
    def _connect(self):
        db=sqlite3.connect(self.path); db.row_factory=sqlite3.Row; db.execute("PRAGMA foreign_keys=ON"); return db
    def create_task(self, task_id: str, goal: str, payload: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO tasks(id,goal,status,payload) VALUES(?,?,?,?)",(task_id,goal,"queued",json.dumps(payload)))
            db.execute("INSERT INTO runs(task_id,event,details) VALUES(?,?,?)",(task_id,"created","{}"))
    def set_status(self, task_id: str, status: str, details: dict[str, Any] | None = None) -> None:
        if status not in {"queued","running","needs_approval","succeeded","failed","cancelled"}: raise ValueError("invalid task status")
        with self._connect() as db:
            cur=db.execute("UPDATE tasks SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,task_id))
            if cur.rowcount != 1: raise KeyError(task_id)
            db.execute("INSERT INTO runs(task_id,event,details) VALUES(?,?,?)",(task_id,status,json.dumps(details or {})))
    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row=db.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
            if row is None: return None
            result=dict(row); result["payload"]=json.loads(result["payload"]); return result
    def list_runs(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows=db.execute("SELECT event,details,created_at FROM runs WHERE task_id=? ORDER BY id",(task_id,)).fetchall()
            return [{**dict(row),"details":json.loads(row["details"])} for row in rows]
