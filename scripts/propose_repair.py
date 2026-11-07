"""Generate a minimal candidate patch from an issue; never merge or deploy."""
import json, os, subprocess, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def gh(*args): return subprocess.check_output(["gh", *args], text=True, cwd=ROOT)
def main():
    key=os.environ.get("GEMINI_API_KEY")
    if not key: raise SystemExit("GEMINI_API_KEY Actions secret is missing")
    n=os.environ["ISSUE_NUMBER"]
    issue=json.loads(gh("issue","view",n,"--repo",os.environ["GITHUB_REPOSITORY"],"--json","title,body"))
    names=subprocess.check_output(["git","ls-files","*.py","*.md","*.toml"],text=True,cwd=ROOT).splitlines()
    files=[]
    for name in names[:80]:
        if any(x in name.lower() for x in (".env","secret","credential","key")): continue
        p=ROOT/name
        if p.is_file() and p.stat().st_size<25000: files.append("\n--- "+name+" ---\n"+p.read_text(errors="replace"))
    prompt=("Return ONLY a minimal unified diff applicable by git apply. Fix the reported bug and add a regression test. Do not change workflows, dependencies, secrets, deployment configuration, or destructive behavior. If evidence is insufficient return exactly NO_SAFE_PATCH.\nISSUE: "+issue.get("title","")+"\n"+issue.get("body","")+"\nFILES:\n"+"".join(files))
    data=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.1,"maxOutputTokens":6000}}).encode()
    req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key="+key,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r: result=json.loads(r.read())
    patch=result["candidates"][0]["content"]["parts"][0]["text"].strip()
    if patch=="NO_SAFE_PATCH": raise SystemExit("No safe patch could be generated")
    if patch.startswith("```"): patch=patch.split("\n",1)[1].rsplit("```",1)[0]
    out=ROOT/"candidate.patch"; out.write_text(patch+"\n")
    subprocess.run(["git","apply","--check",str(out)],cwd=ROOT,check=True)
    subprocess.run(["git","apply",str(out)],cwd=ROOT,check=True); out.unlink(missing_ok=True)
    for row in subprocess.check_output(["git","status","--porcelain"],text=True,cwd=ROOT).splitlines():
        name=row[3:].strip()
        if not name.endswith((".py",".md",".toml")) or any(x in name.lower() for x in (".env","secret","credential","key")): raise SystemExit("Patch touched disallowed path: "+name)
    print("Candidate patch applied; full tests must pass before a draft PR is opened.")
if __name__=="__main__": main()
