import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/evals/scripts"))
from climb import accept, climb, rates, report, score, set_description


def run(**graders):
    return {"graders": [{"name": n.replace("_", "-"), "passed": p} for n, p in graders.items()]}


RESULT = {"cases": [
    {"name": "train-build-a", "promptMarkdown": "---\nname: x\n---\ndeploy the worker\n",
     "arms": {"with": [run(fires_build=True, silent_evals=True),
                       run(fires_build=False, silent_evals=False)]}},
    {"name": "hold-none-b", "promptMarkdown": "retry runs",
     "arms": {"with": [run(silent_build=True, silent_evals=True)]}},
]}


def split(trig, clean):
    return {"trigger": trig, "clean": clean, "fails": []}


class ClimbTest(unittest.TestCase):
    def test_score(self):
        s = score(RESULT)
        self.assertEqual(s["train"]["trigger"]["build"], [1, 2])
        self.assertEqual(s["train"]["clean"], [1, 2])
        self.assertEqual(s["hold"]["clean"], [1, 1])
        self.assertEqual(s["train"]["fails"], [{"miss": "build", "prompt": "deploy the worker"},
                                               {"false_fire": "evals", "prompt": "deploy the worker"}])
        self.assertEqual(rates(s["hold"]), (1.0, 1.0))

    def test_accept(self):
        old = {"hold": split({"build": [2, 4], "evals": [4, 4]}, [8, 8])}
        better = {"hold": split({"build": [3, 4], "evals": [4, 4]}, [8, 8])}
        drop_one = {"hold": split({"build": [4, 4], "evals": [3, 4]}, [8, 8])}
        drop_two = {"hold": split({"build": [4, 4], "evals": [2, 4]}, [8, 8])}
        self.assertTrue(accept(old, better))
        self.assertTrue(accept(old, drop_one))
        self.assertFalse(accept(old, drop_two))
        self.assertFalse(accept(old, old))

    def test_set_description(self):
        md = "---\nname: build\ndescription: old\n---\nbody\ndescription: not this one\n"
        self.assertEqual(set_description(md, "new one"),
                         "---\nname: build\ndescription: new one\n---\nbody\ndescription: not this one\n")
        for bad in ("has: colon", "two\nlines", "x" * 1537, "", "'quoted'", "tag #x"):
            with self.assertRaises(ValueError):
                set_description(md, bad)


    def test_set_description_rejects_more_yaml_breakers(self):
        md = "---\nname: x\ndescription: old\n---\n"
        for bad in ("ends with colon:", "tab:\tafter", "`starts with backtick", "[list", "&anchor use", "- dash"):
            with self.assertRaises(ValueError, msg=bad):
                set_description(md, bad)

    def test_accept_rejects_clean_drop(self):
        old = {"hold": split({"build": [0, 4]}, [8, 8])}
        new = {"hold": split({"build": [4, 4]}, [4, 8])}
        self.assertFalse(accept(old, new))

    def test_report_fails_on_partial_or_empty_hold(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "r.json"
            only_train = {"cases": [RESULT["cases"][0]]}
            p.write_text(json.dumps(only_train))
            self.assertEqual(report(p), 1)
            p.write_text(json.dumps(dict(RESULT, partial=True)))
            self.assertEqual(report(p), 1)

    def test_climb_restores_descriptions_when_a_pass_crashes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "skills/build").mkdir(parents=True)
            f = root / "skills/build/SKILL.md"
            f.write_text("---\nname: build\ndescription: original\n---\n")
            calls = []

            def run_eval(i, budget):
                calls.append(i)
                if i == 0:
                    return {"costUsd": 1.0, "cases": [
                        {"name": "train-build-a", "promptMarkdown": "p",
                         "arms": {"with": [run(fires_build=False)]}}]}
                raise RuntimeError("eval crashed")

            with self.assertRaises(RuntimeError):
                climb(root, 60, 3, "m", run_eval=run_eval,
                      propose_fn=lambda *a: ({"build": "proposed new text"}, 0.5))
            self.assertEqual(calls, [0, 1])
            self.assertIn("description: original", f.read_text())


if __name__ == "__main__":
    unittest.main()
