"""Review-only automatic event clip capture. Does not affect counting."""
from collections import deque
from datetime import datetime
from pathlib import Path
import json
import threading
import time
import shutil
import cv2

class LearningCentre:
    def __init__(self, root):
        self.root = Path(root) / 'learning_centre'
        self.root.mkdir(parents=True, exist_ok=True)
        self.buffer = deque(maxlen=60)
        self.last_sample = 0.0
        self.pending = None
        self.last_auto = 0.0
        self.previous_boxes = None
        self.previous_ids = set()
        self.lock = threading.Lock()

    def ingest(self, frame, live=False):
        if not live:
            return
        now = time.monotonic()
        if now - self.last_sample < 1 / 6:
            return
        self.last_sample = now
        resized = cv2.resize(frame, (640, 360))
        with self.lock:
            self.buffer.append(resized.copy())
            if self.pending:
                self.pending['frames'].append(resized.copy())
                if now >= self.pending['until']:
                    incident = self.pending
                    self.pending = None
                    threading.Thread(target=self._write, args=(incident,), daemon=True).start()

    def trigger(self, reason='Manual review', source='operator'):
        with self.lock:
            if self.pending or not self.buffer:
                return False
            now = time.monotonic()
            self.pending = dict(frames=list(self.buffer), until=now + 10,
                                reason=reason, source=source,
                                created=datetime.now().isoformat(timespec='seconds'))
            return True

    def observe_boxes(self, boxes, live=False):
        """Flag suspicious detection transitions, not proven tyre-count errors.

        boxes: list of (x1,y1,x2,y2,track_id,confidence) tuples.
        The auto-trigger has a 90-second cooldown to limit disk use.
        """
        if not live:
            self.previous_boxes = None
            self.previous_ids.clear()
            return False
        current_count = len(boxes)
        current_ids = {int(b[4]) for b in boxes if len(b) >= 6}
        reason = None
        if self.previous_boxes is not None:
            if self.previous_boxes >= 2 and current_count == 1:
                reason = 'Possible overlap: two or more detections merged into one'
            elif self.previous_boxes >= 2 and current_count == 0:
                reason = 'Unknown event: multiple detections disappeared'
        # A low-confidence detection is a candidate for human review, not a classification.
        if reason is None and any(len(b) >= 6 and float(b[5]) < 0.40 for b in boxes):
            reason = 'Unknown event: low-confidence tyre detection'
        self.previous_boxes = current_count
        self.previous_ids = current_ids
        if reason is None or time.monotonic() - self.last_auto < 90:
            return False
        if self.trigger(reason, 'automatic'):
            self.last_auto = time.monotonic()
            return True
        return False

    def _write(self, incident):
        out = None
        try:
            if shutil.disk_usage(self.root).free < 1024 * 1024 * 1024:
                return
            stem = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            out = self.root / stem
            out.mkdir()
            frames = incident.pop('frames')
            video = cv2.VideoWriter(str(out / 'review.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 6, (640, 360))
            if not video.isOpened():
                raise RuntimeError('Cannot open MP4 writer')
            try:
                for frame in frames:
                    video.write(frame)
            finally:
                video.release()
            incident.update(status='needs_review', actual_tyres=None, notes='',
                            video='review.mp4', frame_count=len(frames))
            (out / 'review.json').write_text(json.dumps(incident, indent=2), encoding='utf-8')
        except Exception:
            if out is not None and out.exists():
                shutil.rmtree(out, ignore_errors=True)

    def list_incidents(self):
        items = []
        for p in sorted(self.root.glob('*/review.json'), reverse=True):
            try:
                item = json.loads(p.read_text(encoding='utf-8'))
                item['folder'] = str(p.parent)
                items.append(item)
            except Exception:
                continue
        return items

    def save_review(self, folder, actual_tyres, notes):
        p = Path(folder).resolve() / 'review.json'
        if self.root.resolve() not in p.parents:
            raise ValueError('Invalid review folder')
        item = json.loads(p.read_text(encoding='utf-8'))
        count = int(actual_tyres)
        if count < 0:
            raise ValueError('Tyre count cannot be negative')
        item.update(status='reviewed', actual_tyres=count, notes=str(notes)[:2000])
        p.write_text(json.dumps(item, indent=2), encoding='utf-8')
