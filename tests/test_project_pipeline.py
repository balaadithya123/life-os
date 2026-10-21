import json, pathlib, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import project_pipeline as p

class PipelineTests(unittest.TestCase):
    def test_required_fields_and_types(self):
        with self.assertRaisesRegex(ValueError,"name"): p.validate_project({"idea":"x"})
        with self.assertRaisesRegex(ValueError,"idea"): p.validate_project({"name":"x"})
        with self.assertRaisesRegex(ValueError,"JSON array"): p.validate_project({"name":"x","idea":"y","features":"no"})
    def test_intake_builds_package_and_manual_gates(self):
        with tempfile.TemporaryDirectory() as d:
            inbox=pathlib.Path(d)/"inbox"; out=pathlib.Path(d)/"state"; inbox.mkdir()
            (inbox/"idea.json").write_text(json.dumps({"name":"Study Helper","idea":"Track revision","features":["planner"]}))
            self.assertEqual(len(p.process_intakes(inbox,out)),1)
            folder=out/"study-helper"; project=json.loads((folder/"project.json").read_text()); tasks=json.loads((folder/"tasks.json").read_text())
            self.assertTrue(project["manual_build_required"]); self.assertTrue(project["manual_publish_required"])
            self.assertTrue(any(t["id"]=="manual_build" and t["requires_user_action"] for t in tasks))
            self.assertIn("Acceptance criteria",(folder/"BUILD_BRIEF.md").read_text())
    def test_bad_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d); (path/"bad.json").write_text("{bad")
            with self.assertRaisesRegex(ValueError,"Invalid JSON"): p.process_intakes(path,path/"out")
    def test_trend_groups_and_ranks_severity(self):
        text=p.report([{"category":"performance","title":"Slow load","severity":"medium"},{"category":"performance","title":"Slow dashboard","severity":"high"},{"category":"security","title":"Access leak","severity":"critical"}],"test")
        self.assertLess(text.index("[CRITICAL] security"),text.index("[HIGH] performance")); self.assertIn("2 evidence item(s)",text)
    def test_empty_data_does_not_invent_trends(self):
        text=p.report([],"test"); self.assertIn("No feedback or observations",text); self.assertNotIn("Prioritised trends",text)

if __name__=="__main__": unittest.main()
