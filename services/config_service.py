"""Leitura e escrita de configuração com valores padrão e escrita atômica."""
import copy
import json
import logging
import os
import tempfile

from paths import CONFIG_PATH, DATA_DIR

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    # Inspeção
    "threshold": 300,       # pixels de borda a partir dos quais a tampa é considerada ausente
    "min_brightness": 50,   # brilho médio mínimo para considerar que há uma garrafa
    "active_recipe": None,  # nome da receita em uso
    # Hardware
    "camera_source": "auto",              # auto | picamera | opencv:<idx> | synthetic
    "rotate_180": True,                   # câmera montada invertida na esteira
    "trigger": {
        "pin": 17,                        # entrada BCM monitorada em paralelo ao botão da tela
    },
    "ejector": {
        "time_ms": 100,                   # duração do pulso do expulsor
    },
    "io": {
        "presence_pin": 27,               # sensor de presença de peça
        "ejection_pin": 22,               # sensor de peça na expulsão
        "ejector_pin": 23,                # saída do expulsor
        "led_pin": 24,                    # saída do LED de trigger
        "active_high": True,
    },
}

def _deep_merge(defaults, saved):
    """Mescla dicts preservando defaults para chaves ausentes."""
    result = copy.deepcopy(defaults)
    if not isinstance(saved, dict):
        return result
    for key, value in saved.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _as_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _normalize(config):
    config["threshold"] = _as_float(config.get("threshold"), DEFAULT_CONFIG["threshold"])
    config["min_brightness"] = _as_float(
        config.get("min_brightness"), DEFAULT_CONFIG["min_brightness"]
    )

    active = config.get("active_recipe")
    config["active_recipe"] = active if isinstance(active, str) and active.strip() else None

    if not isinstance(config.get("camera_source"), str) or not config["camera_source"].strip():
        config["camera_source"] = DEFAULT_CONFIG["camera_source"]

    config["rotate_180"] = bool(config.get("rotate_180", DEFAULT_CONFIG["rotate_180"]))

    trigger = config.get("trigger") or {}
    trigger.pop("mode", None)
    trigger["pin"] = _as_int(trigger.get("pin"), DEFAULT_CONFIG["trigger"]["pin"])
    config["trigger"] = trigger

    ejector = config.get("ejector") or {}
    ejector["time_ms"] = max(0, _as_int(ejector.get("time_ms"), DEFAULT_CONFIG["ejector"]["time_ms"]))
    config["ejector"] = ejector

    io_cfg = config.get("io") or {}
    for key in ("presence_pin", "ejection_pin", "ejector_pin", "led_pin"):
        io_cfg[key] = _as_int(io_cfg.get(key), DEFAULT_CONFIG["io"][key])
    io_cfg["active_high"] = bool(io_cfg.get("active_high", True))
    config["io"] = io_cfg

    return config


def load_config():
    """Carrega a configuração, completando chaves ausentes com os padrões."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    if not CONFIG_PATH.exists():
        save_config(config)
        return config

    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict):
            raise ValueError("configuração deve ser um objeto JSON")
        config = _deep_merge(DEFAULT_CONFIG, saved)
    except (OSError, ValueError) as exc:
        LOGGER.warning("Configuração inválida em %s (%s). Usando padrões.", CONFIG_PATH, exc)
        return copy.deepcopy(DEFAULT_CONFIG)

    return _normalize(config)


def save_config(config):
    """Grava a configuração de forma atômica para evitar arquivo truncado."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=DATA_DIR, prefix=".config-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_name, CONFIG_PATH)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
