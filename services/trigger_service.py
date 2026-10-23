"""Monitora a fonte de trigger configurada (botão da tela ou pino GPIO)."""
import logging

LOGGER = logging.getLogger(__name__)

POLL_INTERVAL_MS = 50


class TriggerService:
    """Monitora a entrada de trigger em paralelo ao botão da tela."""

    def __init__(self, app, io, callback, pin=None):
        self.app = app
        self.io = io
        self.callback = callback
        self.pin = pin
        self._running = False
        self._after_id = None
        self._last_state = False

    def start(self):
        self._running = True
        self._poll()

    def _poll(self):
        if not self._running:
            return
        try:
            state = bool(self.io.read_input("trigger"))
            if state and not self._last_state:
                LOGGER.debug("Trigger acionado no pino %s", self.pin)
                self.callback()
            self._last_state = state
            self._after_id = self.app.after(POLL_INTERVAL_MS, self._poll)
        except Exception:
            LOGGER.exception("Falha ao monitorar o trigger")
            self.stop()

    def stop(self):
        self._running = False
        if self._after_id is not None:
            try:
                self.app.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
