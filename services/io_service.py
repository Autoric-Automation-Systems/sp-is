"""Entradas e saídas digitais.

No Raspberry Pi usa gpiozero (preferencial) ou RPi.GPIO. Sem GPIO disponível,
o serviço funciona em modo simulado, permitindo testar a interface no PC.

Mapa de I/O (BCM):
- presence_pin: sensor de presença de peça
- ejection_pin: sensor de peça na expulsão
- ejector_pin: saída do expulsor
- led_pin: saída do LED de trigger
- trigger.pin: entrada do trigger (quando a fonte é PIN)
"""
import logging
import threading

from services.config_service import load_config

LOGGER = logging.getLogger(__name__)

AVAILABLE_BCM_PINS = [
    2, 3, 4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
]

INPUT_KEYS = ("presence", "ejection", "trigger")
OUTPUT_KEYS = ("ejector", "led")


class _SimulatedBackend:
    name = "simulado"

    def __init__(self, inputs, outputs):
        self._inputs = {name: False for name in inputs}
        self._outputs = {name: False for name in outputs}

    def read_input(self, name):
        return bool(self._inputs.get(name, False))

    def set_simulated_input(self, name, value):
        if name in self._inputs:
            self._inputs[name] = bool(value)

    def write_output(self, name, value):
        if name in self._outputs:
            self._outputs[name] = bool(value)

    def read_output(self, name):
        return bool(self._outputs.get(name, False))

    def close(self):
        pass


class _GpioZeroBackend:
    name = "gpiozero"

    def __init__(self, inputs, outputs, active_high=True):
        from gpiozero import InputDevice, OutputDevice

        self._inputs = {
            name: InputDevice(pin, pull_up=False) for name, pin in inputs.items()
        }
        self._outputs = {
            name: OutputDevice(pin, active_high=active_high, initial_value=False)
            for name, pin in outputs.items()
        }

    def read_input(self, name):
        return bool(self._inputs[name].value)

    def set_simulated_input(self, name, value):
        pass

    def write_output(self, name, value):
        device = self._outputs[name]
        device.on() if value else device.off()

    def read_output(self, name):
        return bool(self._outputs[name].value)

    def close(self):
        for device in list(self._inputs.values()) + list(self._outputs.values()):
            try:
                device.close()
            except Exception:
                pass


class _RPiGpioBackend:
    name = "RPi.GPIO"

    def __init__(self, inputs, outputs, active_high=True):
        import RPi.GPIO as GPIO

        self._gpio = GPIO
        self._inputs = dict(inputs)
        self._outputs = dict(outputs)
        self._active_high = active_high

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in self._inputs.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        for pin in self._outputs.values():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    def read_input(self, name):
        return self._gpio.input(self._inputs[name]) == self._gpio.HIGH

    def set_simulated_input(self, name, value):
        pass

    def write_output(self, name, value):
        level = bool(value) if self._active_high else not value
        self._gpio.output(self._outputs[name], self._gpio.HIGH if level else self._gpio.LOW)

    def read_output(self, name):
        return self._gpio.input(self._outputs[name]) == self._gpio.HIGH

    def close(self):
        try:
            self._gpio.cleanup()
        except Exception:
            pass


def _pin_map(config):
    io_cfg = config["io"]
    inputs = {
        "presence": io_cfg["presence_pin"],
        "ejection": io_cfg["ejection_pin"],
        "trigger": config["trigger"]["pin"],
    }
    outputs = {
        "ejector": io_cfg["ejector_pin"],
        "led": io_cfg["led_pin"],
    }
    return inputs, outputs


def _create_backend(config):
    inputs, outputs = _pin_map(config)
    active_high = config["io"].get("active_high", True)

    pins = list(inputs.values()) + list(outputs.values())
    duplicates = {pin for pin in pins if pins.count(pin) > 1}
    if duplicates:
        LOGGER.warning("Pinos GPIO duplicados na configuração: %s", sorted(duplicates))

    for factory in (
        lambda: _GpioZeroBackend(inputs, outputs, active_high),
        lambda: _RPiGpioBackend(inputs, outputs, active_high),
    ):
        try:
            backend = factory()
            LOGGER.info("I/O iniciado com backend %s (pinos: %s)", backend.name, inputs | outputs)
            return backend
        except Exception as exc:
            LOGGER.info("Backend de I/O indisponível (%s)", exc)

    LOGGER.info("I/O em modo simulado (sem GPIO disponível)")
    return _SimulatedBackend(inputs, outputs)


class IOService:
    def __init__(self):
        self._config = load_config()
        self._backend = _create_backend(self._config)
        self._timers = {}
        self._lock = threading.Lock()

    @property
    def backend_name(self):
        return self._backend.name

    @property
    def simulated(self):
        return self._backend.name == "simulado"

    def read_input(self, name):
        try:
            return self._backend.read_input(name)
        except Exception:
            LOGGER.exception("Falha ao ler entrada %s", name)
            return False

    def read_inputs(self):
        return {name: self.read_input(name) for name in INPUT_KEYS}

    def set_simulated_input(self, name, value):
        self._backend.set_simulated_input(name, value)

    def write_output(self, name, value):
        try:
            self._backend.write_output(name, value)
        except Exception:
            LOGGER.exception("Falha ao escrever saída %s", name)

    def read_output(self, name):
        try:
            return self._backend.read_output(name)
        except Exception:
            return False

    def pulse_output(self, name, duration_ms=100):
        """Liga a saída e desliga após `duration_ms`."""
        duration_ms = max(1, int(duration_ms))
        with self._lock:
            previous = self._timers.get(name)
            if previous is not None:
                previous.cancel()

            self.write_output(name, True)

            def reset():
                self.write_output(name, False)

            timer = threading.Timer(duration_ms / 1000.0, reset)
            timer.daemon = True
            timer.start()
            self._timers[name] = timer
        return duration_ms

    def pin_map(self):
        inputs, outputs = _pin_map(self._config)
        return inputs, outputs

    def close(self):
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        self._backend.close()


_instance = None
_instance_lock = threading.Lock()


def get_io():
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = IOService()
        return _instance


def restart_io():
    global _instance
    with _instance_lock:
        if _instance is not None:
            _instance.close()
            _instance = None
    return get_io()


def shutdown_io():
    global _instance
    with _instance_lock:
        if _instance is not None:
            _instance.close()
            _instance = None
