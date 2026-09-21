from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "asset-extraction" / "scripts" / "index_assets.py"
SPEC = importlib.util.spec_from_file_location("asset_index", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load {SCRIPT}")
ASSET_INDEX = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ASSET_INDEX
SPEC.loader.exec_module(ASSET_INDEX)


class AssetIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="asset-index-test-"))
        (self.root / "a").mkdir()
        (self.root / "z").mkdir()
        (self.root / "node_modules").mkdir()
        (self.root / "a" / "logo.png").write_bytes(b"same asset")
        (self.root / "z" / "logo-copy.png").write_bytes(b"same asset")
        (self.root / "a" / "hero.jpg").write_bytes(b"hero asset")
        (self.root / "a" / "notes.txt").write_text("not an asset", encoding="utf-8")
        (self.root / "node_modules" / "ignored.png").write_bytes(b"ignored")
        self.output = self.root / "artifacts" / "asset-index.jsonl"

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def test_indexes_assets_deduplicates_and_shortlists(self) -> None:
        result = ASSET_INDEX.index_assets(
            self.root,
            self.output,
            keywords=["logo"],
            max_shortlist=1,
        )
        ASSET_INDEX.write_manifest(self.output, result["header"], result["entries"])

        records = [
            json.loads(line) for line in self.output.read_text(encoding="utf-8").splitlines()
        ]
        entries = records[1:]
        paths = {entry["path"] for entry in entries}
        duplicate = next(entry for entry in entries if entry["path"] == "z/logo-copy.png")

        self.assertEqual(paths, {"a/hero.jpg", "a/logo.png", "z/logo-copy.png"})
        self.assertEqual(result["header"]["total_candidates"], 3)
        self.assertEqual(result["header"]["unique_candidates"], 2)
        self.assertEqual(result["header"]["duplicate_files"], 1)
        self.assertEqual(duplicate["duplicate_of"], "a/logo.png")
        self.assertEqual(result["header"]["shortlist"], [{"path": "a/logo.png", "rank_score": 1}])

    def test_include_all_can_inventory_non_media_files(self) -> None:
        result = ASSET_INDEX.index_assets(self.root, self.output, include_all=True)

        paths = {entry["path"] for entry in result["entries"]}
        self.assertIn("a/notes.txt", paths)
        self.assertNotIn("node_modules/ignored.png", paths)

    def test_reuse_requires_an_unchanged_inventory(self) -> None:
        first = ASSET_INDEX.index_assets(self.root, self.output)
        ASSET_INDEX.write_manifest(self.output, first["header"], first["entries"])

        reused = ASSET_INDEX.index_assets(self.root, self.output, reuse=True)
        self.assertTrue(reused["reused"])

        (self.root / "a" / "hero.jpg").write_bytes(b"changed hero asset")
        changed = ASSET_INDEX.index_assets(self.root, self.output, reuse=True)
        self.assertFalse(changed["reused"])


if __name__ == "__main__":
    unittest.main()
