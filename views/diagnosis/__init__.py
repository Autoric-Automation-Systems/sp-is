"""Abas do diagnóstico."""

from .tab_cpu import CpuTab
from .tab_disk import DiskTab
from .tab_gpio import GpioTab
from .tab_io import IoTab
from .tab_mem import MemTab
from .tab_network import NetworkTab
from .tab_system import SystemTab

__all__ = [
    "CpuTab",
    "DiskTab",
    "GpioTab",
    "IoTab",
    "MemTab",
    "NetworkTab",
    "SystemTab",
]
