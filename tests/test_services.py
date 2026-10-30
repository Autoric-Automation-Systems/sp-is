import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

import services.config_service as config_service
import services.recipe_service as recipe_service
from services.config_service import DEFAULT_CONFIG
from services.database import InspectionRepository
from services.inspection_service import InspectionHistory
from services.recipe_service import (
    ROI_COUNT,
    load_reference_image,
    normalize_rois,
    save_recipe,
)
from services.run_cycle import RunCycle
from services.vision_service import (
    clamp_roi,
    crop_roi,
    evaluate_rois,
    match_percent,
    normalize_window,
    parse_percent,
    ssim_percent,
)


def _image(color, size=(48, 64)):
    height, width = size
    return np.full((height, width, 3), color, dtype=np.uint8)


def _roi(x1, y1, x2, y2, name="Tampa", min_match=85.0, max_match=100.0):
    return {
        "name": name,
        "roi": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        "min_match": min_match,
        "max_match": max_match,
    }


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

    def test_defaults_have_no_global_vision_threshold(self):
        config = config_service.load_config()
        self.assertNotIn("threshold", config)
        self.assertNotIn("min_brightness", config)

    def test_merges_missing_keys_with_defaults(self):
        config_service.CONFIG_PATH.write_text(
            json.dumps({"ejector": {"time_ms": 250}}), encoding="utf-8"
        )
        config = config_service.load_config()
        self.assertEqual(config["ejector"]["time_ms"], 250)
        self.assertEqual(
            config["io"]["presence_pin"], config_service.DEFAULT_CONFIG["io"]["presence_pin"]
        )

    def test_legacy_threshold_keys_are_dropped(self):
        config_service.CONFIG_PATH.write_text(
            json.dumps({"threshold": 300, "min_brightness": 50}), encoding="utf-8"
        )
        config = config_service.load_config()
        self.assertNotIn("threshold", config)
        self.assertNotIn("min_brightness", config)

    def test_corrupt_file_falls_back_to_defaults(self):
        config_service.CONFIG_PATH.write_text("{invalido", encoding="utf-8")
        config = config_service.load_config()
        self.assertEqual(config, config_service.DEFAULT_CONFIG)

    def test_roundtrip(self):
        config_service.save_config({"active_recipe": "Pote", "rotate_180": False})
        config = config_service.load_config()
        self.assertEqual(config["active_recipe"], "Pote")
        self.assertFalse(config["rotate_180"])

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

    def _rois(self):
        return [
            _roi(100, 90, 20, 10),
            _roi(200, 300, 260, 360, name="Nível", min_match=80, max_match=95),
            _roi(20, 400, 120, 460, name="Rótulo"),
        ]

    def test_save_and_list_normalizes_both_rois(self):
        ok, error = save_recipe("Pote Teste", self._rois(), self.frame)
        self.assertTrue(ok, error)

        recipes = recipe_service.list_recipes()
        self.assertEqual(len(recipes), 1)
        rois = recipes[0]["rois"]
        self.assertEqual(len(rois), ROI_COUNT)
        self.assertEqual([entry["name"] for entry in rois], ["Tampa", "Nível", "Rótulo"])
        # Coordenadas ordenadas de x1/y1/x2/y2.
        self.assertEqual(rois[0]["roi"], {"x1": 20, "y1": 10, "x2": 100, "y2": 90})
        self.assertEqual(rois[1]["min_match"], 80.0)
        self.assertEqual(rois[1]["max_match"], 95.0)
        self.assertTrue((self.images_dir / "pote_teste.jpg").exists())

        data = json.loads((self.recipes_dir / "pote_teste.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["rois"]), ROI_COUNT)
        self.assertNotIn("roi", data)

    def test_default_window_when_missing(self):
        rois = [{"name": "A", "roi": {"x1": 0, "y1": 0, "x2": 10, "y2": 10}}]
        normalized = normalize_rois(rois)
        self.assertEqual(len(normalized), ROI_COUNT)
        self.assertEqual(normalized[0]["min_match"], 85.0)
        self.assertEqual(normalized[0]["max_match"], 100.0)
        self.assertEqual(normalized[0]["name"], "A")

    def test_rejects_duplicate_name(self):
        self.assertTrue(save_recipe("Pote", self._rois(), self.frame)[0])
        ok, error = save_recipe("Pote", self._rois(), self.frame)
        self.assertFalse(ok)
        self.assertIn("existe", error)

    def test_rejects_duplicate_roi_names(self):
        rois = [_roi(0, 0, 10, 10, name="Igual"), _roi(20, 20, 40, 40, name="igual")]
        ok, error = save_recipe("Duplicada", rois, self.frame)
        self.assertFalse(ok)
        self.assertIn("3 ROIs", error)

        full = [
            _roi(0, 0, 10, 10, name="Igual"),
            _roi(20, 20, 40, 40, name="igual"),
            _roi(50, 50, 60, 60, name="Outro"),
        ]
        ok, error = save_recipe("Duplicada", full, self.frame)
        self.assertFalse(ok)
        self.assertIn("nome diferente", error)

    def test_rejects_invalid_window(self):
        rois = [_roi(0, 0, 10, 10, min_match=99, max_match=90), _roi(20, 20, 40, 40, name="B")]
        # Janela invertida é reordenada na normalização, nunca salva inválida.
        normalized = normalize_rois(rois)
        self.assertLessEqual(normalized[0]["min_match"], normalized[0]["max_match"])

    def test_rejects_roi_with_zero_area(self):
        rois = [{"name": "A", "roi": {"x1": 10, "y1": 10, "x2": 10, "y2": 20}}]
        ok, error = save_recipe("Zero", rois, self.frame)
        self.assertFalse(ok)
        self.assertIn("3 ROIs", error)

        zero = [
            _roi(10, 10, 10, 20, name="A"),
            _roi(20, 20, 40, 40, name="B"),
            _roi(50, 50, 60, 60, name="C"),
        ]
        ok, error = save_recipe("Zero", zero, self.frame)
        self.assertFalse(ok)
        self.assertIn("área válida", error)

    def test_rename_removes_old_files_and_keeps_created_at(self):
        self.assertTrue(save_recipe("Antigo", self._rois(), self.frame)[0])
        created_at = recipe_service.list_recipes()[0]["created_at"]

        ok, error = save_recipe("Novo", self._rois(), self.frame, original_name="Antigo")
        self.assertTrue(ok, error)
        self.assertFalse((self.recipes_dir / "antigo.json").exists())
        self.assertFalse((self.images_dir / "antigo.jpg").exists())
        recipes = recipe_service.list_recipes()
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]["name"], "Novo")
        self.assertEqual(recipes[0]["created_at"], created_at)

    def test_ignores_corrupt_recipe_files(self):
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        (self.recipes_dir / "quebrada.json").write_text("{nao e json", encoding="utf-8")
        self.assertEqual(recipe_service.list_recipes(), [])

    def test_migrates_legacy_single_roi_recipe(self):
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        legacy = {
            "name": "Legado",
            "image": "data/images/legado.jpg",
            "roi": {"x1": 275, "y1": 0, "x2": 365, "y2": 31},
        }
        (self.recipes_dir / "legado.json").write_text(
            json.dumps(legacy), encoding="utf-8"
        )

        recipes = recipe_service.list_recipes()
        self.assertEqual(len(recipes), 1)
        rois = recipes[0]["rois"]
        self.assertEqual(len(rois), ROI_COUNT)
        self.assertEqual(rois[0]["roi"], {"x1": 275, "y1": 0, "x2": 365, "y2": 31})
        self.assertEqual(rois[0]["name"], "Tampa")
        self.assertEqual(rois[1]["name"], "Nível")
        self.assertEqual(rois[2]["name"], "ROI 3")
        # Os ROIs criados ficam logo abaixo do original.
        self.assertGreaterEqual(rois[1]["roi"]["y1"], rois[0]["roi"]["y2"])
        self.assertEqual(rois[1]["roi"]["x1"], rois[0]["roi"]["x1"])
        # ROI inventado entra permissivo: não reprova peça até ser calibrado.
        for index in (1, 2):
            self.assertEqual(rois[index]["min_match"], 0.0)
            self.assertEqual(rois[index]["max_match"], 100.0)
        self.assertNotIn("roi", recipes[0])

    def test_pads_recipe_saved_with_fewer_rois(self):
        """Receita gravada com 2 ROIs ganha o terceiro, inerte, ao ser carregada."""
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "name": "Dois",
            "image": "data/images/dois.jpg",
            "rois": [
                _roi(0, 0, 40, 40),
                _roi(0, 100, 40, 140, name="Nível", min_match=80, max_match=95),
            ],
        }
        (self.recipes_dir / "dois.json").write_text(json.dumps(data), encoding="utf-8")

        rois = recipe_service.list_recipes()[0]["rois"]
        self.assertEqual(len(rois), ROI_COUNT)
        self.assertEqual(rois[1]["min_match"], 80.0)
        self.assertEqual(rois[2]["min_match"], 0.0)
        self.assertEqual(rois[2]["max_match"], 100.0)

    def test_delete_removes_json_and_image(self):
        self.assertTrue(save_recipe("Apagar", self._rois(), self.frame)[0])
        recipe = recipe_service.list_recipes()[0]
        self.assertTrue(recipe_service.delete_recipe(recipe))
        self.assertEqual(recipe_service.list_recipes(), [])
        self.assertFalse((self.images_dir / "apagar.jpg").exists())

    def test_load_reference_image(self):
        self.assertTrue(save_recipe("Ref", self._rois(), _image((10, 20, 30), (480, 640)))[0])
        recipe = recipe_service.list_recipes()[0]
        frame = load_reference_image(recipe)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[:2], (480, 640))
        self.assertIsNone(load_reference_image({"image": "data/images/inexistente.jpg"}))


class VisionServiceTests(unittest.TestCase):
    def test_crop_roi_clamps_and_orders(self):
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        cropped = crop_roi(frame, {"x1": 250, "y1": 50, "x2": -20, "y2": 150})
        self.assertEqual(cropped.shape[:2], (50, 200))

    def test_clamp_roi_rejects_zero_area(self):
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        self.assertIsNone(clamp_roi({"x1": 10, "y1": 10, "x2": 10, "y2": 20}, frame.shape))

    def test_identical_roi_scores_full_match(self):
        reference = _image((120, 130, 140))
        self.assertEqual(match_percent(reference, reference, {"x1": 0, "y1": 0, "x2": 32, "y2": 24}), 100.0)

    def test_ssim_orders_similar_images(self):
        base = np.full((48, 64), 128, dtype=np.uint8)
        noisy = base.copy()
        noisy[:, 32:] = 10

        similar = base.copy()
        similar[:, 32:] = 120

        self.assertGreater(ssim_percent(base, similar), ssim_percent(base, noisy))

    def test_normalize_window_orders_and_clamps(self):
        self.assertEqual(normalize_window(90, 80), (80.0, 90.0))
        self.assertEqual(normalize_window(-5, 250), (0.0, 100.0))
        self.assertEqual(normalize_window(None, None), (85.0, 100.0))

    def test_window_accepts_comma_decimal_separator(self):
        # Teclado numérico pt-BR digita "88,5" nos campos do editor.
        self.assertEqual(parse_percent("88,5"), 88.5)
        self.assertEqual(normalize_window("88,5", "97,5"), (88.5, 97.5))
        self.assertIsNone(parse_percent("8o"))
        self.assertIsNone(parse_percent(""))
        self.assertIsNone(parse_percent(None))

    def test_evaluate_rois_approves_when_inside_window(self):
        reference = _image((90, 120, 150))
        frame = reference.copy()
        rois = [_roi(0, 0, 32, 24), _roi(32, 0, 64, 24, name="Nível")]

        result = evaluate_rois(frame, reference, rois)
        self.assertTrue(result["valid"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], "OK")
        self.assertEqual(result["score"], 100.0)
        self.assertEqual([entry["name"] for entry in result["rois"]], ["Tampa", "Nível"])

    def test_evaluate_rois_reports_all_failing_roi_names(self):
        reference = _image((90, 120, 150))
        frame = np.zeros_like(reference)
        rois = [_roi(0, 0, 32, 24), _roi(32, 0, 64, 24, name="Nível")]

        result = evaluate_rois(frame, reference, rois)
        self.assertTrue(result["valid"])
        self.assertFalse(result["ok"])
        # Todos os ROIs reprovados aparecem, não só o primeiro.
        self.assertEqual(result["failed"], ["Tampa", "Nível"])
        self.assertEqual(result["result"], "ERRO: TAMPA + NÍVEL")
        self.assertLess(result["score"], 85.0)
        self.assertEqual(len(result["rois"]), 2)
        self.assertEqual(result["rois"][0]["x1"], 0)
        self.assertEqual(result["rois"][0]["x2"], 32)

    def test_evaluate_rois_lists_only_the_failing_rois(self):
        reference = _image((90, 120, 150))
        frame = reference.copy()
        frame[:, :32] = 0  # reprova só o primeiro ROI
        rois = [_roi(0, 0, 32, 24), _roi(32, 0, 64, 24, name="Nível")]

        result = evaluate_rois(frame, reference, rois)
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed"], ["Tampa"])
        self.assertEqual(result["result"], "ERRO: TAMPA")
        self.assertTrue(result["rois"][1]["ok"])

    def test_window_can_reject_too_different_and_accept_mid_range(self):
        reference = _image((90, 120, 150))
        frame = np.full_like(reference, 100)  # cinza próximo, mas não idêntico

        strict = evaluate_rois(frame, reference, [_roi(0, 0, 32, 24, min_match=99.0)])
        self.assertFalse(strict["ok"])

        loose = evaluate_rois(frame, reference, [_roi(0, 0, 32, 24, min_match=0.0, max_match=100.0)])
        self.assertTrue(loose["ok"])

    def test_evaluate_rois_without_reference(self):
        result = evaluate_rois(_image((1, 2, 3)), None, [_roi(0, 0, 10, 10)])
        self.assertFalse(result["valid"])
        self.assertEqual(result["result"], "SEM REFERÊNCIA")
        self.assertFalse(result["ok"])

    def test_evaluate_rois_with_invalid_roi(self):
        reference = _image((1, 2, 3))
        result = evaluate_rois(reference, reference, [_roi(10, 10, 10, 20)])
        self.assertFalse(result["valid"])
        self.assertEqual(result["result"], "ROI INVÁLIDO")


class InspectionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = InspectionRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.repo.close()

    def _history(self):
        return InspectionHistory(repository=self.repo, maxlen=50)

    def _result(self, result, ok, elapsed_ms, frame, match=100.0, details=None):
        return {
            "timestamp": None,
            "recipe": "Pote",
            "result": result,
            "ok": ok,
            "match": match,
            "elapsed_ms": elapsed_ms,
            "frame": frame,
            "details": details if details is not None else [
                {"name": "Tampa", "match": match, "min": 85.0, "max": 100.0, "ok": ok,
                 "x1": 10, "y1": 20, "x2": 60, "y2": 70},
                {"name": "Nível", "match": match, "min": 80.0, "max": 100.0, "ok": ok,
                 "x1": 10, "y1": 100, "x2": 60, "y2": 160},
            ],
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
        history.add_result(self._result("OK", True, 20, frame, match=97.5))
        history.add_result(self._result("ERRO: TAMPA", False, 30, frame, match=40.0))

        stats = history.stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["ok"], 2)
        self.assertEqual(stats["nok"], 1)
        self.assertAlmostEqual(stats["approval"], 66.666, places=2)
        self.assertAlmostEqual(stats["avg_ms"], 20.0)
        self.assertEqual(stats["by_result"]["OK"], 2)
        self.assertEqual(stats["by_recipe"]["Pote"]["total"], 3)

        recent = history.recent(2)
        self.assertEqual([record.result for record in recent], ["ERRO: TAMPA", "OK"])
        self.assertEqual(recent[1].match, 97.5)
        self.assertEqual(len(recent[0].details), 2)
        self.assertEqual(recent[0].details[0]["name"], "Tampa")
        self.assertEqual(recent[0].details[0]["x1"], 10)
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
        first.add_result(self._result("OK", True, 5, frame, match=91.0))

        second = self._history()
        self.assertEqual(second.stats()["total"], 1)
        self.assertEqual(len(second.recent(5)), 1)
        self.assertEqual(second.recent(1)[0].result, "OK")
        self.assertEqual(second.recent(1)[0].match, 91.0)
        self.assertEqual(len(second.recent(1)[0].details), 2)

    def test_clear_removes_everything(self):
        history = self._history()
        history.add_result(self._result("OK", True, 5, np.zeros((8, 8, 3), np.uint8)))
        history.clear()
        self.assertEqual(history.stats()["total"], 0)
        self.assertEqual(history.recent(5), [])


class DatabaseMigrationTests(unittest.TestCase):
    OLD_SCHEMA = """
    CREATE TABLE inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        recipe TEXT NOT NULL,
        result TEXT NOT NULL,
        ok INTEGER NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        threshold REAL NOT NULL DEFAULT 0,
        brightness REAL NOT NULL DEFAULT 0,
        elapsed_ms INTEGER NOT NULL DEFAULT 0,
        frame_jpeg BLOB
    );
    """

    def test_adds_new_columns_and_keeps_old_rows(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "legacy.db"

        conn = sqlite3.connect(path)
        conn.executescript(self.OLD_SCHEMA)
        conn.execute(
            "INSERT INTO inspections (timestamp, recipe, result, ok, score, threshold,"
            " brightness, elapsed_ms) VALUES ('2026-01-01 10:00:00', 'Pote', 'OK', 1, 42, 300, 90, 12)"
        )
        conn.commit()
        conn.close()

        repo = InspectionRepository(path)
        try:
            self.assertEqual(repo.count(), 1)
            record = repo.recent(1)[0]
            self.assertEqual(record.result, "OK")
            self.assertEqual(record.match, 0.0)
            self.assertEqual(record.details, [])
        finally:
            repo.close()


class RoiSelectorTests(unittest.TestCase):
    """Seleção por mouse em coordenadas da imagem, com múltiplos ROIs."""

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
        self.changes = []
        self.selector = ROISelector(
            self.canvas,
            scale=0.8,
            image_size=(640, 480),
            on_change=self.changes.append,
        )

    class _Event:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    def test_draw_by_drag_maps_to_image_coordinates(self):
        self.selector.set_regions([None, None])
        self.selector.on_click(self._Event(80, 40))
        self.selector.on_drag(self._Event(400, 300))
        self.selector.on_release(self._Event(400, 300))
        self.assertEqual(
            self.selector.get_final_roi(0),
            {"x1": 100, "y1": 50, "x2": 500, "y2": 375},
        )
        self.assertTrue(self.changes)

    def test_draw_clamps_to_image_bounds(self):
        self.selector.set_regions([None, None])
        self.selector.on_click(self._Event(0, 0))
        self.selector.on_drag(self._Event(600, 500))
        self.selector.on_release(self._Event(600, 500))
        roi = self.selector.get_final_roi(0)
        self.assertLessEqual(roi["x2"], 640)
        self.assertLessEqual(roi["y2"], 480)

    def test_click_inside_other_region_selects_it(self):
        first = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
        second = {"x1": 300, "y1": 300, "x2": 400, "y2": 400}
        self.selector.set_regions([first, second])
        self.assertEqual(self.selector.active, 0)

        # (240, 240) no canvas = (300, 300) na imagem: dentro do segundo ROI.
        self.selector.on_click(self._Event(240, 240))
        self.selector.on_release(self._Event(240, 240))

        self.assertEqual(self.selector.active, 1)
        self.assertEqual(self.selector.get_final_roi(0), first)
        self.assertEqual(self.selector.get_final_roi(1), second)

    def test_drag_moves_only_the_active_region(self):
        first = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
        second = {"x1": 300, "y1": 300, "x2": 400, "y2": 400}
        self.selector.set_regions([first, second])
        self.selector.set_active(1)

        # Arrasta o segundo ROI 50 px (imagem) para a direita e para baixo.
        self.selector.on_click(self._Event(280, 280))
        self.selector.on_drag(self._Event(320, 320))
        self.selector.on_release(self._Event(320, 320))

        self.assertEqual(self.selector.get_final_roi(0), first)
        moved = self.selector.get_final_roi(1)
        self.assertEqual(moved["x1"], 350)
        self.assertEqual(moved["y1"], 350)
        self.assertEqual(moved["x2"] - moved["x1"], 100)
        self.assertEqual(moved["y2"] - moved["y1"], 100)

    def test_set_region_mirrors_numeric_fields(self):
        self.selector.set_regions([None, None])
        self.selector.set_region(1, {"x1": 10, "y1": 20, "x2": 30, "y2": 40})
        self.assertEqual(
            self.selector.get_regions()[1],
            {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
        )


class _FakeIO:
    def __init__(self):
        self.pulses = []

    def pulse_output(self, name, duration_ms=100):
        self.pulses.append(name)

    def read_input(self, name):
        return False


class RunCycleTests(unittest.TestCase):
    """Decisão do ciclo: aprovação por ROI, expulsor e gravação no histórico."""

    def _view(self, recipe, frame):
        class View:
            def __init__(self):
                self.app = SimpleNamespace(current_recipe=recipe)
                self.camera = SimpleNamespace(get_frame=lambda timeout=1.0: frame)
                self.time_label = SimpleNamespace(configure=lambda **kwargs: None)
                self.status_calls = []

            def set_status(self, text, color, rois=None):
                self.status_calls.append((text, rois))

        return View()

    def _run(self, recipe, frame, reference):
        io = _FakeIO()
        view = self._view(recipe, frame)
        with mock.patch("services.run_cycle.get_io", return_value=io), \
                mock.patch("services.run_cycle.load_config", return_value=DEFAULT_CONFIG), \
                mock.patch("services.run_cycle.load_reference_image", return_value=reference):
            result = RunCycle(view).run()
        return result, view, io

    def _recipe(self, min_match=85.0, max_match=100.0):
        return {
            "name": "Pote",
            "rois": [
                _roi(0, 0, 32, 24, name="Tampa", min_match=min_match, max_match=max_match),
                _roi(32, 0, 64, 24, name="Nível", min_match=min_match, max_match=max_match),
                _roi(0, 24, 32, 48, name="Rótulo", min_match=min_match, max_match=max_match),
            ],
        }

    def test_approved_part_is_recorded_without_ejection(self):
        frame = _image((90, 120, 150))
        result, view, io = self._run(self._recipe(), frame, frame.copy())

        self.assertEqual(result["result"], "OK")
        self.assertTrue(result["ok"])
        self.assertTrue(result["record"])
        self.assertEqual(result["match"], 100.0)
        self.assertEqual(len(result["details"]), ROI_COUNT)
        self.assertIn("led", io.pulses)
        self.assertNotIn("ejector", io.pulses)
        self.assertEqual(view.status_calls[-1][0], "OK")

    def test_rejected_part_ejects_and_records_failing_roi(self):
        reference = _image((255, 255, 255))
        frame = _image((0, 0, 0))
        result, view, io = self._run(self._recipe(), frame, reference)

        # Os três ROIs reprovam: o resultado lista todos.
        self.assertEqual(result["result"], "ERRO: TAMPA + NÍVEL + RÓTULO")
        self.assertFalse(result["ok"])
        self.assertTrue(result["record"])
        self.assertIn("ejector", io.pulses)
        self.assertEqual(view.status_calls[-1][0], "ERRO: TAMPA + NÍVEL + RÓTULO")

    def test_permissive_window_never_ejects(self):
        reference = _image((255, 255, 255))
        frame = _image((0, 0, 0))
        result, _view, io = self._run(
            self._recipe(min_match=0.0, max_match=100.0), frame, reference
        )

        self.assertEqual(result["result"], "OK")
        self.assertNotIn("ejector", io.pulses)

    def test_missing_reference_is_not_recorded(self):
        result, view, io = self._run(self._recipe(), _image((10, 10, 10)), None)

        self.assertEqual(result["result"], "SEM REFERÊNCIA")
        self.assertFalse(result["record"])
        self.assertNotIn("ejector", io.pulses)
        self.assertEqual(view.status_calls[-1][0], "SEM REFERÊNCIA")

    def test_missing_recipe_is_not_recorded(self):
        result, _view, io = self._run(None, _image((10, 10, 10)), None)

        self.assertEqual(result["result"], "SEM RECEITA")
        self.assertFalse(result["record"])
        self.assertNotIn("ejector", io.pulses)


if __name__ == "__main__":
    unittest.main()
