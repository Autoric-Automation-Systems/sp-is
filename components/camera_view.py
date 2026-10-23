"""Fonte de vídeo única do aplicativo.

Backends disponíveis:
- picamera2: Raspberry Pi (câmera CSI)
- opencv: webcam USB ou câmera V4L2
- synthetic: frames gerados em memória, para desenvolvimento sem hardware

Seleção por `SPIS_CAMERA` (auto | picamera | opencv | synthetic). Em `auto`,
tenta picamera2, depois OpenCV e, por fim, o simulador.

Contrato: `get_frame()` retorna uma imagem BGR (numpy) ou None se não houver
frame disponível. A captura roda em thread própria para não bloquear a UI.
"""
import glob
import logging
import os
import sys
import threading
import time

import cv2
import numpy as np

from services.config_service import load_config

LOGGER = logging.getLogger(__name__)

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_INTERVAL = 0.03


class PicameraBackend:
    name = "picamera"

    def __init__(self, camera_num=0):
        from picamera2 import Picamera2

        self.picam2 = Picamera2(camera_num=int(camera_num))
        size = (FRAME_WIDTH, FRAME_HEIGHT)
        try:
            config = self.picam2.create_preview_configuration(
                main={"size": size, "format": "RGB888"}
            )
            self._rgb = True
        except Exception:
            # Fallback: formato padrão do Picamera2 (memória em ordem BGRX).
            config = self.picam2.create_preview_configuration(main={"size": size})
            self._rgb = False
        self.picam2.configure(config)
        self.picam2.set_controls({
            "ExposureTime": 0,
            "AnalogueGain": 0,
            "AeEnable": True,
            "AwbEnable": True,
        })
        self.picam2.start()
        time.sleep(0.2)

    def read(self):
        frame = self.picam2.capture_array()
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]
        if self._rgb:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame

    def close(self):
        try:
            self.picam2.stop()
        finally:
            self.picam2.close()


class OpenCVBackend:
    def __init__(self, index=None):
        index = int(index if index is not None else os.environ.get("SPIS_CAMERA_INDEX", "0"))
        self.name = f"opencv:{index}"
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.cap.release()
            raise RuntimeError(f"câmera OpenCV {index} não disponível")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    def read(self):
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("falha ao ler frame da câmera OpenCV")
        return cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    def close(self):
        self.cap.release()


class SyntheticBackend:
    """Câmera simulada: cena com garrafa e tampa alternando a cada 4 s.

    A cena é desenhada na orientação "correta" (texto legível). O giro de 180°
    é aplicado depois, por `orient_frame`, exatamente como em uma câmera real.
    """

    name = "synthetic"

    def __init__(self):
        self._started_at = time.monotonic()

    def read(self):
        elapsed = time.monotonic() - self._started_at
        frame = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), (24, 28, 34), dtype=np.uint8)

        for x in range(0, FRAME_WIDTH, 40):
            cv2.line(frame, (x, 0), (x, FRAME_HEIGHT), (34, 40, 52), 1)
        for y in range(0, FRAME_HEIGHT, 40):
            cv2.line(frame, (0, y), (FRAME_WIDTH, y), (34, 40, 52), 1)

        # Garrafa: corpo, gargalo e tampa na região do ROI (315, 132)-(399, 173)
        cv2.rectangle(frame, (250, 250), (390, 470), (70, 82, 105), -1)
        cv2.rectangle(frame, (280, 150), (360, 250), (60, 72, 92), -1)

        has_cap = int(elapsed // 4) % 2 == 0
        if has_cap:
            cv2.ellipse(frame, (320, 150), (44, 16), 0, 0, 360, (205, 212, 220), -1)
        else:
            cv2.ellipse(frame, (320, 150), (40, 15), 0, 0, 360, (35, 35, 38), -1)
            for radius in range(12, 45, 6):
                cv2.circle(frame, (320, 150), radius, (225, 225, 225), 2)

        cv2.putText(frame, "CAMERA SIMULADA (DEV)", (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 200, 255), 2)
        cv2.putText(frame, "TAMPA" if has_cap else "SEM TAMPA", (16, 64),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (120, 220, 150) if has_cap else (90, 90, 240), 2)
        cv2.putText(frame, time.strftime("%H:%M:%S"), (16, FRAME_HEIGHT - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 190, 200), 1)
        return frame

    def close(self):
        pass


def _configured_source():
    """SPIS_CAMERA tem precedência sobre a configuração salva."""
    env_source = os.environ.get("SPIS_CAMERA")
    if env_source:
        return env_source.strip().lower()
    return str(load_config().get("camera_source", "auto")).strip().lower()


def _parse_source(source):
    source = (source or "auto").strip().lower()
    if source.startswith("opencv"):
        _, _, index = source.partition(":")
        try:
            return "opencv", int(index or 0)
        except ValueError:
            return "opencv", 0
    if source.startswith("picamera"):
        _, _, index = source.partition(":")
        try:
            return "picamera", int(index or 0)
        except ValueError:
            return "picamera", 0
    if source.startswith("synthetic"):
        return "synthetic", None
    return "auto", None


def _build_backend(name, argument=None):
    if name == "picamera":
        return PicameraBackend(argument or 0)
    if name == "opencv":
        return OpenCVBackend(argument if argument is not None else 0)
    if name == "synthetic":
        return SyntheticBackend()
    raise ValueError(f"backend desconhecido: {name}")


def _create_backend(source=None):
    requested, argument = _parse_source(source if source is not None else _configured_source())

    if requested == "auto":
        candidates = [("picamera", 0), ("opencv", 0), ("synthetic", None)]
    elif requested == "synthetic":
        candidates = [("synthetic", None)]
    else:
        # Fonte explícita indisponível não pode impedir o app de abrir.
        candidates = [(requested, argument), ("synthetic", None)]

    errors = []
    for name, arg in candidates:
        backend = None
        try:
            backend = _build_backend(name, arg)
            if name != "synthetic":
                for _ in range(3):
                    try:
                        backend.read()
                        break
                    except Exception:
                        time.sleep(0.2)
                else:
                    raise RuntimeError("câmera não retornou frames")
            LOGGER.info("Câmera iniciada: %s", backend.name)
            return backend
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            if name != "synthetic" and requested not in ("auto", "synthetic"):
                LOGGER.warning("Câmera %s indisponível (%s); usando simulada", name, exc)
            if backend is not None:
                try:
                    backend.close()
                except Exception:
                    pass
            LOGGER.info("Backend de câmera %s indisponível (%s)", name, exc)

    raise RuntimeError("nenhum backend de câmera disponível: " + "; ".join(errors))


def _v4l2_devices():
    """Lista câmeras V4L2 usando sysfs (inclui a webcam do notebook)."""
    cameras = []
    sysfs_nodes = sorted(glob.glob("/sys/class/video4linux/video*"))

    for entry in sysfs_nodes:
        node = os.path.basename(entry)
        suffix = node.replace("video", "")
        if not suffix.isdigit():
            continue
        try:
            with open(os.path.join(entry, "index"), encoding="utf-8") as handle:
                if int(handle.read().strip()) != 0:
                    continue  # nós de metadados (ex.: video1 de uma webcam UVC)
        except (OSError, ValueError):
            pass
        try:
            with open(os.path.join(entry, "name"), encoding="utf-8") as handle:
                name = handle.read().strip()
        except OSError:
            name = f"Câmera V4L2 {node}"
        cameras.append({
            "source": f"opencv:{suffix}",
            "label": f"{name} ({node})",
        })

    if not sysfs_nodes:
        for device in sorted(glob.glob("/dev/video*")):
            suffix = device.replace("/dev/video", "")
            if suffix.isdigit():
                cameras.append({
                    "source": f"opencv:{suffix}",
                    "label": f"Câmera USB / V4L2 ({device})",
                })

    return cameras


def orient_frame(frame, rotate_180=True):
    """Aplica o giro de 180° usado quando a câmera é montada invertida."""
    if frame is None or not rotate_180:
        return frame
    return cv2.rotate(frame, cv2.ROTATE_180)


def list_available_cameras():
    """Lista fontes de vídeo disponíveis no sistema.

    Retorna uma lista de dicts com `source` (valor salvo na configuração) e `label`.
    """
    cameras = []

    try:
        from picamera2 import Picamera2

        for index, info in enumerate(Picamera2.global_camera_info()):
            model = info.get("Model") or info.get("model") or "CSI"
            cameras.append({
                "source": "picamera" if index == 0 else f"picamera:{index}",
                "label": f"Câmera CSI ({model})",
            })
    except Exception:
        pass

    video_devices = _v4l2_devices()
    cameras.extend(video_devices)

    if not video_devices and not sys.platform.startswith("linux"):
        # Windows/macOS: sonda índices comuns sem manter o dispositivo aberto.
        for index in range(4):
            capture = cv2.VideoCapture(index)
            try:
                if capture.isOpened():
                    cameras.append({
                        "source": f"opencv:{index}",
                        "label": f"Câmera {index} (OpenCV)",
                    })
            finally:
                capture.release()

    cameras.append({"source": "synthetic", "label": "Câmera simulada (desenvolvimento)"})
    cameras.append({"source": "auto", "label": "Automática (detectar ao iniciar)"})
    return cameras


class CameraView:
    def __init__(self, backend=None):
        self._backend = backend or _create_backend()
        self._lock = threading.Lock()
        self._frame = None
        self._last_error = None
        self._running = threading.Event()
        self._running.set()
        self._thread = threading.Thread(target=self._capture_loop, name="camera", daemon=True)
        self._thread.start()

    @property
    def backend_name(self):
        return self._backend.name

    def _capture_loop(self):
        while self._running.is_set():
            try:
                frame = self._backend.read()
            except Exception as exc:
                self._last_error = str(exc)
                LOGGER.debug("Falha na captura: %s", exc)
                time.sleep(0.5)
                continue

            with self._lock:
                self._frame = frame
            time.sleep(FRAME_INTERVAL)

    def get_frame(self, timeout=1.0):
        """Retorna o frame mais recente em BGR, aguardando até `timeout` segundos."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self._frame is not None:
                    return self._frame.copy()
            time.sleep(0.01)
        return None

    def stop(self):
        self._running.clear()
        self._thread.join(timeout=2)
        try:
            self._backend.close()
        except Exception:
            LOGGER.exception("Falha ao encerrar a câmera")


_instance = None
_instance_lock = threading.Lock()


def get_camera():
    """Retorna a instância compartilhada da câmera (criada sob demanda)."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = CameraView()
        return _instance


def shutdown_camera():
    global _instance
    with _instance_lock:
        if _instance is not None:
            _instance.stop()
            _instance = None


def current_backend_name():
    """Backend em uso, sem inicializar a câmera."""
    with _instance_lock:
        return _instance.backend_name if _instance is not None else None


def restart_camera(source=None):
    """Reinicia a câmera (usado ao trocar a fonte nas Configurações)."""
    global _instance
    with _instance_lock:
        if _instance is not None:
            _instance.stop()
            _instance = None
        backend = _create_backend(source)
        _instance = CameraView(backend)
        return _instance.backend_name
