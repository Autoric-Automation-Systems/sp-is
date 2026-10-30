"""Família tipográfica padrão de cada plataforma.

O tema é o mesmo no Raspberry Pi (Linux) e no PC (Windows/macOS); apenas a
família muda para a que já vem instalada no sistema, evitando que o Tkinter
substitua a fonte por outra de métricas diferentes.

`SPIS_FONT` permite forçar outra família (útil em distros sem DejaVu Sans).
"""
import os
import platform

_PLATFORM_FAMILIES = {
    "Windows": "Segoe UI",
    "Linux": "DejaVu Sans",
    "Darwin": "Helvetica Neue",
}


def family() -> str:
    """Família padrão do sistema operacional atual (ou `SPIS_FONT`)."""
    override = (os.environ.get("SPIS_FONT") or "").strip()
    if override:
        return override
    return _PLATFORM_FAMILIES.get(platform.system(), "TkDefaultFont")
