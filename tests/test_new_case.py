import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/evals/scripts"))
from new_case import split_for, write_case


class NewCaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for s in ("build", "evals"):
            (self.root / "skills" / s).mkdir(parents=True)
            (self.root / "skills" / s / "SKILL.md").write_text("---\nname: x\n---\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_confusion_graders(self):
        case = write_case(self.root, "missing-key", "my key is gone", "evals")
        self.assertEqual(case.name, f"{split_for('missing-key')}-evals-missing-key")
        fires = (case / "graders/fires-evals.md").read_text()
        silent = (case / "graders/silent-build.md").read_text()
        self.assertIn("tool: Skill", fires)
        self.assertNotIn("max: 0", fires)
        self.assertIn("min: 0\nmax: 0", silent)
        self.assertIn('(?:[\\w-]+:)?build"', silent)

    def test_none_expect_has_only_silent_graders(self):
        case = write_case(self.root, "retry-runs", "retry the runs", "none")
        self.assertEqual(sorted(p.name for p in (case / "graders").iterdir()),
                         ["silent-build.md", "silent-evals.md"])

    def test_depth_graders_and_tags(self):
        case = write_case(self.root, "supa", "add a migration", "build",
                          reads=["references/supabase.md"], skips=["references/cloudflare.md"], smoke=True)
        self.assertIn(r"references/supabase\.md", (case / "graders/reads-supabase.md").read_text())
        self.assertIn("max: 0", (case / "graders/skips-cloudflare.md").read_text())
        prompt = (case / "prompt.md").read_text()
        self.assertIn("smoke", prompt)
        self.assertIn("depth", prompt)
        self.assertIn("max_turns: 6", prompt)

    def test_split_is_stable(self):
        self.assertEqual(split_for("abc"), split_for("abc"))
        splits = [split_for(f"s{i}") for i in range(1000)]
        self.assertTrue(550 < splits.count("train") < 650)

    def test_rejects_repeat_bad_slug_and_bad_expect(self):
        write_case(self.root, "one", "p", "build")
        with self.assertRaises(FileExistsError):
            write_case(self.root, "one", "p", "build")
        with self.assertRaises(ValueError):
            write_case(self.root, "Bad Slug", "p", "build")
        with self.assertRaises(ValueError):
            write_case(self.root, "two", "p", "nope")


if __name__ == "__main__":
    unittest.main()
