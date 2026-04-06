import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start()

    def start(self):
        if self.process:
            self.process.kill()

        print("🔁 Reiniciando app...")
        self.process = subprocess.Popen(["python", "app.py"])

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            self.start()


if __name__ == "__main__":
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()