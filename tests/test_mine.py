import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/evals/scripts"))
from mine import invocations, scrub, user_text

MAP = {"evals": "evals", "grill-rounds": "grill", "trigger-recipes": "none"}


def user(text, **extra):
    return json.dumps({"type": "user", "message": {"content": text}, **extra})


def skill(name):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}})


class MineTest(unittest.TestCase):
    def test_scrub(self):
        out = scrub("mail me@x.io key sk-abcdefghijklmnop1234 in /home/bob/repo "
                    "<pasted_content id=\"1\">teammate: x@y.com says\n\nthe sync broke</pasted_content id=\"1\"> ok")
        for bad in ("me@x.io", "x@y.com", "sk-abcdefghijklmnop1234", "/home/bob", "<pasted_content"):
            self.assertNotIn(bad, out)
        self.assertIn("[pasted: teammate: <email> says the sync broke]", out)
        self.assertTrue(out.endswith("ok"))
        self.assertLess(len(scrub("<pasted_content>" + "a " * 1000 + "</pasted_content>")), 420)

    def test_user_text_skips_harness_meta_and_tool_results(self):
        self.assertIsNone(user_text(json.loads(user("<command-name>/clear</command-name>"))))
        self.assertIsNone(user_text(json.loads(user("Base directory for this skill", isMeta=True))))
        self.assertIsNone(user_text(json.loads(json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "content": "x"}]}}))))
        self.assertEqual(user_text(json.loads(user("  <pasted_content id=\"a\">x</pasted_content id=\"a\">"))),
                         "<pasted_content id=\"a\">x</pasted_content id=\"a\">")
        self.assertEqual(user_text(json.loads(json.dumps({"type": "user", "message": {"content": [
            {"type": "text", "text": "hello"}]}}))), "hello")

    def test_invocations_keep_opening_and_last_three(self):
        lines = [user("open: which env has the api key"), user("a"), user("b"), user("c"), user("d"),
                 skill("evals"), skill("unknown-skill"), skill("charlesdr-dev-loop:grill-rounds"),
                 "not json"]
        got = list(invocations(lines, MAP))
        self.assertEqual([g["expect"] for g in got], ["evals", "grill"])
        self.assertEqual(got[0]["opening"], "open: which env has the api key")
        self.assertEqual(got[0]["context"], ["b", "c", "d"])
        self.assertEqual(got[1]["old_skill"], "grill-rounds")

    def test_no_opening_no_candidate(self):
        self.assertEqual(list(invocations([skill("evals")], MAP)), [])


    def test_scrub_mac_windows_paths_and_more_keys(self):
        out = scrub("/Users/alice/x and C:\\Users\\Alice\\y key tr_dev_abcDEF1234567890123 password=hunter2xyz")
        for bad in ("alice", "Alice", "tr_dev_abc", "hunter2xyz"):
            self.assertNotIn(bad, out)

    def test_scrub_keeps_ordinary_words(self):
        for ok in ("--dangerously-skip-permissions", "skills-retired-2026-10-13", "pk-sorted list"):
            self.assertEqual(scrub(ok), ok)


if __name__ == "__main__":
    unittest.main()
