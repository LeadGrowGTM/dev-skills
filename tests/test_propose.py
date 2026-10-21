import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/evals/scripts"))
from propose import valid
from make_cases import build


class ProposeTest(unittest.TestCase):
    def test_valid_filters(self):
        rows = [
            {"slug": "ok-one", "expect": "build", "prompt": "p", "source": "mined", "i": 3},
            {"slug": "ok-one", "expect": "build", "prompt": "dup", "source": "mined"},
            {"slug": "Bad Slug", "expect": "build", "prompt": "p", "source": "mined"},
            {"slug": "two", "expect": "nope", "prompt": "p", "source": "mined"},
            {"slug": "three", "expect": "none", "prompt": "", "source": "mined"},
            {"slug": "four", "expect": "none", "prompt": "p", "source": "near-miss"},
        ]
        got = valid(rows, {"build", "none"})
        self.assertEqual([r["slug"] for r in got], ["ok-one", "four"])
        self.assertNotIn("i", got[0])

    def test_build_marks_smoke_and_skips_repeats(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "skills/build").mkdir(parents=True)
            (root / "skills/build/SKILL.md").write_text("---\nname: build\n---\n")
            rows = [{"slug": f"case-{i:02d}", "expect": "build", "prompt": "p", "source": "paraphrase"} for i in range(20)]
            self.assertEqual(build(root, rows), (20, 0))
            smoke = [p for p in (root / "evals").glob("*/prompt.md") if "smoke" in p.read_text()]
            self.assertLessEqual(len(smoke), 8)
            self.assertGreaterEqual(len(smoke), 4)
            self.assertEqual(build(root, rows), (0, 20))


    def test_claude_p_runs_with_no_tools_and_no_mcp(self):
        from propose import claude_p_argv
        argv = claude_p_argv("the prompt", "m")
        self.assertEqual(argv[:3], ["claude", "-p", "the prompt"])
        self.assertIn("--strict-mcp-config", argv)
        self.assertEqual(argv[-2:], ["--tools", ""])


if __name__ == "__main__":
    unittest.main()
