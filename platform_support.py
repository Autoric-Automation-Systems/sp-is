"""Detecção da plataforma e dos recursos de hardware disponíveis.

O aplicativo tem dois alvos:

- Raspberry Pi (Linux): câmera CSI via picamera2 e I/O físico via gpiozero.
- PC (Windows, macOS ou Linux de mesa): webcam via OpenCV e I/O simulado.

Este módulo concentra as decisões de plataforma para que o restante do código
não dependa diretamente de `sys.platform`, de caminhos `/sys` ou de
bibliotecas exclusivas do Raspberry Pi.
"""
import functools
import platform
import sys

WINDOWS = sys.platform.startswith("win")
MACOS = sys.platform == "darwin"
LINUX = sys.platform.startswith("linux")

SYSTEM_NAME = platform.system() or sys.platform

_MODEL_PATHS = (
    "/proc/device-tree/model",
    "/sys/firmware/devicetree/base/model",
)
_CPUINFO_PATH = "/proc/cpuinfo"


@functools.lru_cache(maxsize=1)
def is_raspberry_pi() -> bool:
    """True quando o sistema roda em um Raspberry Pi."""
    if not LINUX:
        return False

    for path in _MODEL_PATHS:
        try:
            with open(path, encoding="utf-8", errors="ignore") as handle:
                if "raspberry" in handle.read().lower():
                    return True
        except OSError:
            continue

    try:
        with open(_CPUINFO_PATH, encoding="utf-8", errors="ignore") as handle:
            return "raspberry pi" in handle.read().lower()
    except OSError:
        return False


def system_label() -> str:
    """Nome legível da plataforma, usado nas telas de diagnóstico e nos logs."""
    label = f"{SYSTEM_NAME} {platform.release()}".strip()
    machine = platform.machine()
    if machine:
        label += f" ({machine})"
    if is_raspberry_pi():
        label += " · Raspberry Pi"
    return label


def io_hardware_supported() -> bool:
    """GPIO físico só existe no Linux (gpiozero/RPi.GPIO)."""
    return LINUX


def csi_camera_supported() -> bool:
    """picamera2/libcamera só existem no Linux (CSI no Raspberry Pi)."""
    return LINUX
