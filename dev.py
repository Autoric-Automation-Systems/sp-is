"""Recarrega o aplicativo quando um arquivo .py é alterado (desenvolvimento)."""
import logging
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

LOGGER = logging.getLogger(__name__)


class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start()

    def start(self):
        self.stop()
        LOGGER.info("Iniciando app...")
        self.process = subprocess.Popen([sys.executable, "app.py"])

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        if "__pycache__" in event.src_path:
            return
        LOGGER.info("Alteração detectada em %s", event.src_path)
        self.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        event_handler.stop()
        observer.join()
