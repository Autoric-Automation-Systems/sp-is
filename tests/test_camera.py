"""Testes da câmera simulada (imagens de data/simulation + cena gerada)."""
import os
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from components.camera_view import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    SyntheticBackend,
    _fit_frame,
    _frame_index,
)


def _write_image(path, color, size=(240, 320)):
    """Grava um PNG de cor sólida usando imencode (funciona em caminhos unicode)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = size
    image = np.full((height, width, 3), color, dtype=np.uint8)
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("falha ao codificar a imagem de teste")
    buffer.tofile(str(path))


class SimulationFramesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "simulation"

    def test_frame_index_cycles_through_images(self):
        self.assertEqual(_frame_index(4, 0.0, 4.0), 0)
        self.assertEqual(_frame_index(4, 3.9, 4.0), 0)
        self.assertEqual(_frame_index(4, 4.1, 4.0), 1)
        self.assertEqual(_frame_index(4, 16.0, 4.0), 0)
        self.assertEqual(_frame_index(0, 10.0, 4.0), 0)

    def test_fit_frame_fills_frame_without_distortion(self):
        wide = np.zeros((720, 1280, 3), dtype=np.uint8)
        fitted = _fit_frame(wide)
        self.assertEqual(fitted.shape, (FRAME_HEIGHT, FRAME_WIDTH, 3))

        tall = np.zeros((1000, 500, 3), dtype=np.uint8)
        self.assertEqual(_fit_frame(tall).shape, (FRAME_HEIGHT, FRAME_WIDTH, 3))

        exact = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        self.assertIs(_fit_frame(exact), exact)

    def test_uses_images_from_the_simulation_folder(self):
        _write_image(self.folder / "01.png", (0, 0, 255))  # vermelho em BGR
        backend = SyntheticBackend(frames_dir=self.folder, interval=4.0)
        try:
            frame = backend.read()
        finally:
            backend.close()

        self.assertEqual(frame.shape, (FRAME_HEIGHT, FRAME_WIDTH, 3))
        center = frame[FRAME_HEIGHT // 2, FRAME_WIDTH // 2]
        self.assertTrue(np.allclose(center, (0, 0, 255), atol=2))

    def test_alternates_between_images(self):
        _write_image(self.folder / "a.png", (0, 0, 255))
        _write_image(self.folder / "b.png", (0, 255, 0))
        backend = SyntheticBackend(frames_dir=self.folder, interval=1.0)
        try:
            first = backend.read()
            backend._started_at -= 1.0
            second = backend.read()
        finally:
            backend.close()

        self.assertFalse(np.allclose(first[240, 320], second[240, 320]))
        self.assertTrue(np.allclose(first[240, 320], (0, 0, 255), atol=2))
        self.assertTrue(np.allclose(second[240, 320], (0, 255, 0), atol=2))

    def test_falls_back_to_generated_scene_without_images(self):
        backend = SyntheticBackend(frames_dir=self.folder, interval=4.0)
        try:
            frame = backend.read()
        finally:
            backend.close()

        self.assertTrue(self.folder.is_dir())
        self.assertEqual(frame.shape, (FRAME_HEIGHT, FRAME_WIDTH, 3))
        self.assertGreater(int(frame.max()), 100)  # cena desenhada, não vazia

    def test_ignores_unsupported_files(self):
        self.folder.mkdir(parents=True)
        (self.folder / "leiame.txt").write_text("não é imagem", encoding="utf-8")
        backend = SyntheticBackend(frames_dir=self.folder, interval=4.0)
        try:
            self.assertEqual(backend._images, [])
            self.assertEqual(backend.read().shape, (FRAME_HEIGHT, FRAME_WIDTH, 3))
        finally:
            backend.close()

    def test_replacing_an_image_with_the_same_name_is_reloaded(self):
        """Trocar o conteúdo de 5.jpg não pode continuar mostrando a imagem antiga."""
        path = self.folder / "5.png"
        _write_image(path, (0, 0, 255))  # vermelho
        backend = SyntheticBackend(frames_dir=self.folder, interval=4.0)
        try:
            first = backend.read()
            self.assertTrue(np.allclose(first[240, 320], (0, 0, 255), atol=2))

            # Mesmo nome, conteúdo novo e data de modificação posterior.
            _write_image(path, (0, 255, 0))  # verde
            stamp = path.stat().st_mtime + 5
            os.utime(path, (stamp, stamp))

            backend._scan()
            second = backend.read()
            self.assertTrue(np.allclose(second[240, 320], (0, 255, 0), atol=2))
        finally:
            backend.close()


if __name__ == "__main__":
    unittest.main()
