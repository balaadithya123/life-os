import tempfile
import unittest
from pathlib import Path
from agent_office.engine import TaskStore, WorkflowValidationError, run_workflow, validate_workflow

def workflow(tool="utc_now", args=None):
    return {"name":"test","goal":"exercise safe workflow","steps":[{"id":"s1","tool":tool,"args":args or {}}]}

class AgentOfficeTests(unittest.TestCase):
    def test_valid_workflow(self): self.assertEqual(validate_workflow(workflow())["name"],"test")
    def test_rejects_unknown_tool(self):
        with self.assertRaises(WorkflowValidationError): validate_workflow(workflow("shell"))
    def test_rejects_duplicate_ids(self):
        value=workflow(); value["steps"].append({"id":"s1","tool":"utc_now","args":{}})
        with self.assertRaises(WorkflowValidationError): validate_workflow(value)
    def test_side_effect_waits_for_approval(self): self.assertEqual(run_workflow(workflow("github_open_pr"))["status"],"needs_approval")
    def test_file_reader_confined_to_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"safe.txt").write_text("ok",encoding="utf-8")
            result=run_workflow(workflow("read_project_file",{"path":"safe.txt"}),root)
            self.assertEqual(result["results"][0]["result"]["content"],"ok")
            with self.assertRaises(Exception): run_workflow(workflow("read_project_file",{"path":"../escape.txt"}),root)
    def test_sqlite_persists_tasks_and_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=TaskStore(Path(tmp)/"state.sqlite3"); store.create_task("t1","demo",{"steps":[]}); store.set_status("t1","running")
            self.assertEqual(store.get_task("t1")["status"],"running")
            self.assertEqual([e["event"] for e in store.list_runs("t1")],["created","running"])

if __name__ == "__main__": unittest.main()
