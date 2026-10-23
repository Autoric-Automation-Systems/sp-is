"""Histórico e estatísticas das inspeções, persistidos em SQL."""
import logging
from collections import deque
from datetime import datetime, time

import cv2

from services.database import InspectionRecord, InspectionRepository

LOGGER = logging.getLogger(__name__)

FRAME_JPEG_QUALITY = 80


class InspectionHistory:
    """Fachada de histórico/estatísticas sobre o repositório SQL."""

    def __init__(self, repository=None, maxlen=50):
        self.repository = repository or InspectionRepository()
        self._maxlen = maxlen
        self._records = deque(maxlen=maxlen)
        self.started_at = datetime.combine(datetime.now().date(), time.min)
        self.refresh()

    def refresh(self):
        self._records = deque(
            reversed(self.repository.recent(self._maxlen)), maxlen=self._maxlen
        )

    def _encode_frame(self, frame):
        if frame is None:
            return None
        try:
            ok, encoded = cv2.imencode(
                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), FRAME_JPEG_QUALITY]
            )
            return encoded.tobytes() if ok else None
        except cv2.error:
            LOGGER.exception("Falha ao codificar o frame da inspeção")
            return None

    def add_result(self, result):
        record = InspectionRecord(
            timestamp=result.get("timestamp") or datetime.now(),
            recipe=result.get("recipe") or "-",
            result=result.get("result", "-"),
            ok=bool(result.get("ok")),
            score=int(result.get("score") or 0),
            threshold=float(result.get("threshold") or 0),
            brightness=float(result.get("brightness") or 0),
            elapsed_ms=int(result.get("elapsed_ms") or 0),
            frame_jpeg=self._encode_frame(result.get("frame")),
        )
        self.repository.save(record)
        self._records.append(record)
        return record

    def recent(self, count=10):
        if count <= 0:
            return []
        return list(reversed(list(self._records)[-count:]))

    @property
    def records(self):
        return tuple(self._records)

    def clear(self):
        self.repository.clear()
        self._records.clear()

    def stats(self):
        return self.repository.stats(since=self.started_at)

    def close(self):
        self.repository.close()
