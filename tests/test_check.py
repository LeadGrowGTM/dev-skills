import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check import check

GOOD = "---\nname: {n}\ndescription: Use when testing the {n} skill.\n---\n# {n}\nRead references/a.md for depth.\n"


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".claude-plugin").mkdir()
        (self.root / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "dev-skills", "version": "0.1.0"}))
        refs = self.root / "skills/evals/references"
        refs.mkdir(parents=True)
        (refs / "a.md").write_text("depth\n")
        self.skill = self.root / "skills/evals/SKILL.md"
        self.skill.write_text(GOOD.format(n="evals"))

    def tearDown(self):
        self.tmp.cleanup()

    def fails(self):
        return check(self.root)[0]

    def test_good_plugin_passes_and_warns_missing(self):
        fails, warns = check(self.root)
        self.assertEqual(fails, [])
        self.assertIn("missing skill build", warns)

    def test_unknown_skill_fails(self):
        (self.root / "skills/extra").mkdir()
        self.assertTrue(any("extra" in f for f in self.fails()))

    def test_name_mismatch_fails(self):
        self.skill.write_text(GOOD.format(n="build"))
        self.assertTrue(any("name field" in f for f in self.fails()))

    def test_long_description_fails(self):
        self.skill.write_text(GOOD.format(n="evals").replace("Use when testing", "x" * 1600))
        self.assertTrue(any("chars" in f for f in self.fails()))

    def test_colon_space_in_description_fails(self):
        self.skill.write_text(GOOD.format(n="evals").replace("Use when", "Use when: "))
        self.assertTrue(any("': '" in f for f in self.fails()))

    def test_folded_description_fails(self):
        self.skill.write_text("---\nname: evals\ndescription: >-\n  folded\n---\nreferences/a.md\n")
        self.assertTrue(any("must start with a letter" in f for f in self.fails()))

    def test_long_body_fails(self):
        self.skill.write_text(GOOD.format(n="evals") + "line\n" * 150)
        self.assertTrue(any("body is" in f for f in self.fails()))

    def test_unlinked_reference_fails(self):
        (self.root / "skills/evals/references/orphan.md").write_text("x\n")
        self.assertTrue(any("orphan.md" in f for f in self.fails()))

    def test_dead_link_fails(self):
        self.skill.write_text(GOOD.format(n="evals") + "Run scripts/gone.py\n")
        self.assertTrue(any("scripts/gone.py" in f for f in self.fails()))

    def test_home_path_fails(self):
        (self.root / "skills/evals/references/a.md").write_text("see /home/someone/x\n")
        self.assertTrue(any("machine-specific" in f for f in self.fails()))

    def test_pycache_is_ignored(self):
        cache = self.root / "skills/evals/scripts/__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.cpython-314.pyc").write_bytes(b"\x00/home/someone/x.py")
        self.assertEqual(self.fails(), [])

    def test_trailing_colon_and_backtick_start_fail(self):
        for desc in ("Use when this happens:", "`lg` is the CLI"):
            self.skill.write_text(GOOD.format(n="evals").replace("Use when testing the evals skill.", desc))
            self.assertTrue(self.fails(), desc)

    def test_home_path_in_command_fails_but_not_in_citation(self):
        ref = self.root / "skills/evals/references/a.md"
        ref.write_text("- run `node /home/someone/x/tool.mjs` <!-- src: /home/someone/x/README.md -->\n")
        self.assertTrue(any("machine-specific" in f for f in self.fails()))
        ref.write_text("- run `node tool.mjs` from your clone <!-- src: /home/someone/x/README.md --> (src: /home/someone/y.md)\n")
        self.assertEqual(self.fails(), [])


if __name__ == "__main__":
    unittest.main()
