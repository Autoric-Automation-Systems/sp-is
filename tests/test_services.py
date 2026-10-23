import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

import services.config_service as config_service
import services.recipe_service as recipe_service
from services.database import InspectionRepository
from services.inspection_service import InspectionHistory
from services.vision_service import compare_roi, crop_roi


class ConfigServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._original = (config_service.CONFIG_PATH, config_service.DATA_DIR)
        config_service.CONFIG_PATH = self.root / "config.json"
        config_service.DATA_DIR = self.root

    def tearDown(self):
        config_service.CONFIG_PATH, config_service.DATA_DIR = self._original

    def test_creates_defaults_when_missing(self):
        config = config_service.load_config()
        self.assertEqual(config, config_service.DEFAULT_CONFIG)
        self.assertTrue(config_service.CONFIG_PATH.exists())

    def test_merges_missing_keys_with_defaults(self):
        config_service.CONFIG_PATH.write_text(json.dumps({"threshold": 123}), encoding="utf-8")
        config = config_service.load_config()
        self.assertEqual(config["threshold"], 123)
        self.assertEqual(config["min_brightness"], config_service.DEFAULT_CONFIG["min_brightness"])

    def test_corrupt_file_falls_back_to_defaults(self):
        config_service.CONFIG_PATH.write_text("{invalido", encoding="utf-8")
        config = config_service.load_config()
        self.assertEqual(config, config_service.DEFAULT_CONFIG)

    def test_roundtrip(self):
        config_service.save_config({"threshold": 10, "min_brightness": 20})
        config = config_service.load_config()
        self.assertEqual(config["threshold"], 10)
        self.assertEqual(config["min_brightness"], 20)

    def test_nested_defaults_are_merged(self):
        config_service.CONFIG_PATH.write_text(
            json.dumps({"trigger": {"pin": 27}, "ejector": {"time_ms": 250}}),
            encoding="utf-8",
        )
        config = config_service.load_config()
        self.assertEqual(config["trigger"]["pin"], 27)
        self.assertNotIn("mode", config["trigger"])
        self.assertEqual(config["ejector"]["time_ms"], 250)
        self.assertEqual(config["camera_source"], "auto")
        self.assertEqual(config["io"]["presence_pin"], config_service.DEFAULT_CONFIG["io"]["presence_pin"])

    def test_invalid_trigger_pin_falls_back(self):
        config_service.CONFIG_PATH.write_text(
            json.dumps({"trigger": {"pin": "abc"}, "ejector": {"time_ms": -5}}),
            encoding="utf-8",
        )
        config = config_service.load_config()
        self.assertEqual(config["trigger"]["pin"], config_service.DEFAULT_CONFIG["trigger"]["pin"])
        self.assertEqual(config["ejector"]["time_ms"], 0)


class RecipeServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.recipes_dir = root / "recipes"
        self.images_dir = root / "images"
        self._original = (recipe_service.RECIPES_DIR, recipe_service.IMAGES_DIR)
        recipe_service.RECIPES_DIR = self.recipes_dir
        recipe_service.IMAGES_DIR = self.images_dir
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def tearDown(self):
        recipe_service.RECIPES_DIR, recipe_service.IMAGES_DIR = self._original

    def test_save_and_list_normalizes_roi(self):
        ok, error = recipe_service.save_recipe(
            "Pote Teste", {"x1": 100, "y1": 90, "x2": 20, "y2": 10}, self.frame
        )
        self.assertTrue(ok, error)

        recipes = recipe_service.list_recipes()
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]["roi"], {"x1": 20, "y1": 10, "x2": 100, "y2": 90})
        self.assertTrue((self.images_dir / "pote_teste.jpg").exists())

    def test_rejects_duplicate_name(self):
        self.assertTrue(recipe_service.save_recipe("Pote", {"x1": 0, "y1": 0, "x2": 10, "y2": 10}, self.frame)[0])
        ok, error = recipe_service.save_recipe("Pote", {"x1": 0, "y1": 0, "x2": 10, "y2": 10}, self.frame)
        self.assertFalse(ok)
        self.assertIn("existe", error)

    def test_rename_removes_old_files_and_keeps_created_at(self):
        self.assertTrue(recipe_service.save_recipe("Antigo", {"x1": 0, "y1": 0, "x2": 10, "y2": 10}, self.frame)[0])
        created_at = recipe_service.list_recipes()[0]["created_at"]

        ok, error = recipe_service.save_recipe(
            "Novo", {"x1": 0, "y1": 0, "x2": 10, "y2": 10}, self.frame, original_name="Antigo"
        )
        self.assertTrue(ok, error)
        self.assertFalse((self.recipes_dir / "antigo.json").exists())
        self.assertFalse((self.images_dir / "antigo.jpg").exists())
        recipes = recipe_service.list_recipes()
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]["name"], "Novo")
        self.assertEqual(recipes[0]["created_at"], created_at)

    def test_rejects_roi_outside_frame(self):
        ok, error = recipe_service.save_recipe(
            "Fora", {"x1": 900, "y1": 700, "x2": 1000, "y2": 800}, self.frame
        )
        self.assertFalse(ok)
        self.assertIn("ROI", error)

    def test_ignores_corrupt_recipe_files(self):
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        (self.recipes_dir / "quebrada.json").write_text("{nao e json", encoding="utf-8")
        self.assertEqual(recipe_service.list_recipes(), [])

    def test_delete_removes_json_and_image(self):
        self.assertTrue(recipe_service.save_recipe("Apagar", {"x1": 0, "y1": 0, "x2": 10, "y2": 10}, self.frame)[0])
        recipe = recipe_service.list_recipes()[0]
        self.assertTrue(recipe_service.delete_recipe(recipe))
        self.assertEqual(recipe_service.list_recipes(), [])
        self.assertFalse((self.images_dir / "apagar.jpg").exists())


class VisionServiceTests(unittest.TestCase):
    def test_crop_roi_clamps_and_orders(self):
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        cropped = crop_roi(frame, {"x1": 250, "y1": 50, "x2": -20, "y2": 150})
        self.assertEqual(cropped.shape[:2], (50, 200))

    def test_invalid_roi_is_reported(self):
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        result = compare_roi(frame, {"x1": 10, "y1": 10, "x2": 10, "y2": 20}, 100)
        self.assertFalse(result["valid"])
        self.assertIsNone(result["missing_cap"])

    def test_smooth_region_has_fewer_edges_than_rings(self):
        smooth = np.full((120, 120, 3), 200, dtype=np.uint8)
        rings = np.full((120, 120, 3), 200, dtype=np.uint8)
        for radius in range(10, 55, 5):
            cv2.circle(rings, (60, 60), radius, (30, 30, 30), 2)

        roi = {"x1": 0, "y1": 0, "x2": 120, "y2": 120}
        smooth_result = compare_roi(smooth, roi, 100)
        rings_result = compare_roi(rings, roi, 100)

        self.assertGreater(rings_result["edge_score"], smooth_result["edge_score"])
        self.assertFalse(smooth_result["missing_cap"])
        self.assertTrue(rings_result["missing_cap"])


class InspectionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = InspectionRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.repo.close()

    def _history(self):
        return InspectionHistory(repository=self.repo, maxlen=50)

    def _result(self, result, ok, elapsed_ms, frame):
        return {
            "timestamp": None,
            "recipe": "Pote",
            "result": result,
            "ok": ok,
            "score": 10,
            "threshold": 300,
            "brightness": 100,
            "elapsed_ms": elapsed_ms,
            "frame": frame,
        }

    def test_empty_stats(self):
        stats = self._history().stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["approval"], 0.0)
        self.assertEqual(stats["by_result"], {})

    def test_stats_recent_and_frame_roundtrip(self):
        history = self._history()
        frame = np.full((48, 64, 3), 120, dtype=np.uint8)

        history.add_result(self._result("OK", True, 10, frame))
        history.add_result(self._result("OK", True, 20, frame))
        history.add_result(self._result("ERRO: SEM TAMPA", False, 30, frame))

        stats = history.stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["ok"], 2)
        self.assertEqual(stats["nok"], 1)
        self.assertAlmostEqual(stats["approval"], 66.666, places=2)
        self.assertAlmostEqual(stats["avg_ms"], 20.0)
        self.assertEqual(stats["by_result"]["OK"], 2)
        self.assertEqual(stats["by_recipe"]["Pote"]["total"], 3)

        recent = history.recent(2)
        self.assertEqual([record.result for record in recent], ["ERRO: SEM TAMPA", "OK"])
        decoded = recent[0].frame_bgr()
        self.assertEqual(decoded.shape, frame.shape)

    def test_history_is_bounded_but_database_keeps_all(self):
        history = InspectionHistory(repository=self.repo, maxlen=3)
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        for _ in range(5):
            history.add_result(self._result("OK", True, 1, frame))
        self.assertEqual(len(history.records), 3)
        self.assertEqual(self.repo.count(), 5)

    def test_history_persists_across_instances(self):
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        first = self._history()
        first.add_result(self._result("OK", True, 5, frame))

        second = self._history()
        self.assertEqual(second.stats()["total"], 1)
        self.assertEqual(len(second.recent(5)), 1)
        self.assertEqual(second.recent(1)[0].result, "OK")

    def test_clear_removes_everything(self):
        history = self._history()
        history.add_result(self._result("OK", True, 5, np.zeros((8, 8, 3), np.uint8)))
        history.clear()
        self.assertEqual(history.stats()["total"], 0)
        self.assertEqual(history.recent(5), [])


if __name__ == "__main__":
    unittest.main()


class RoiSelectorTests(unittest.TestCase):
    """Mapeamento canvas → imagem quando o canvas é reduzido."""

    def setUp(self):
        import tkinter as tk

        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("sem display disponível")
        self.addCleanup(self.root.destroy)
        self.root.withdraw()

        from components.roi_selector import ROISelector

        self.canvas = tk.Canvas(self.root, width=512, height=384)
        self.selector = ROISelector(self.canvas, scale=0.8, image_size=(640, 480))

    class _Event:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    def test_draw_by_drag_maps_to_image_coordinates(self):
        self.selector.on_click(self._Event(80, 40))
        self.selector.on_drag(self._Event(400, 300))
        self.selector.on_release(self._Event(400, 300))
        self.assertEqual(
            self.selector.get_final_roi(),
            {"x1": 100, "y1": 50, "x2": 500, "y2": 375},
        )

    def test_draw_clamps_to_image_bounds(self):
        self.selector.on_click(self._Event(0, 0))
        self.selector.on_drag(self._Event(600, 500))
        self.selector.on_release(self._Event(600, 500))
        roi = self.selector.get_final_roi()
        self.assertLessEqual(roi["x2"], 640)
        self.assertLessEqual(roi["y2"], 480)
