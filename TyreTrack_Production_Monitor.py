from datetime import datetime
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()

matches = []
for path in HERE.glob("*.py"):
    if path.resolve() == SELF:
        continue
    text = path.read_text(encoding="utf-8-sig")
    if all(marker in text for marker in (
        "class OakSource:",
        "class CounterWorker(QThread):",
        "class Main(QMainWindow):",
    )):
        matches.append((path, text))

if len(matches) != 1:
    raise SystemExit(
        "No files changed. Expected exactly one main TyreTrack .py file; found: "
        + ", ".join(path.name for path, _ in matches)
    )

source, original = matches[0]
edited = original


def replace_once(old, new, description):
    global edited
    found = edited.count(old)
    if found != 1:
        raise SystemExit(
            f"No files changed. '{description}' matched {found} times "
            "instead of once. Send me this message and your main file's name."
        )
    edited = edited.replace(old, new, 1)


replace_once(
    '''        if "class_confidence" not in columns:
            con.execute(
                "ALTER TABLE counts "
                "ADD COLUMN class_confidence REAL DEFAULT 0"
            )''',
    '''        if "class_confidence" not in columns:
            con.execute(
                "ALTER TABLE counts "
                "ADD COLUMN class_confidence REAL DEFAULT 0"
            )

        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_counts_source_metric "
            "ON counts(source, metric_utc)"
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_counts_source_ts "
            "ON counts(source, ts)"
        )''',
    "database indexes",
)

replace_once(
    '''        rows = con.execute("SELECT ts, metric_utc FROM counts WHERE source=? ORDER BY id", (OAK_NAME,)).fetchall()''',
    '''        rows = con.execute(
            """
            SELECT ts, metric_utc FROM counts
            WHERE source = ?
              AND (
                  (metric_utc IS NOT NULL
                   AND metric_utc >= ? AND metric_utc <= ?)
                  OR
                  (metric_utc IS NULL
                   AND ts >= ? AND ts <= ?)
              )
            """,
            (
                OAK_NAME,
                day_start.timestamp(),
                effective.timestamp(),
                day_start.replace(tzinfo=None).isoformat(),
                effective.replace(tzinfo=None).isoformat(),
            ),
        ).fetchall()''',
    "dashboard history query",
)

replace_once(
    '''    def _capture_loop(self):
        last_packet_at = time.monotonic()

        try:''',
    '''    def _capture_loop(self):
        last_packet_at = time.monotonic()
        capture_interval_start = last_packet_at
        capture_frames = 0

        try:''',
    "camera capture measurement setup",
)

replace_once(
    '''                frame = packet.getCvFrame()

                oak_frame_received()''',
    '''                frame = packet.getCvFrame()

                capture_frames += 1
                capture_elapsed = time.monotonic() - capture_interval_start
                if capture_elapsed >= 10:
                    log(
                        f"PERF OAK capture: "
                        f"fps={capture_frames / capture_elapsed:.1f}, "
                        f"record_queue={self.record_queue.qsize()}, "
                        f"record_drops={self.record_drops}"
                    )
                    capture_interval_start = time.monotonic()
                    capture_frames = 0

                oak_frame_received()''',
    "independent camera capture measurement",
)

replace_once(
    '''    counted = pyqtSignal(int, float)''',
    '''    counted = pyqtSignal(int, float, int)''',
    "counted signal",
)

replace_once(
    '''            self.status.emit("Loading tyre detector...")
            model = YOLO(str(model_path))''',
    '''            self.status.emit("Loading tyre detector...")
            # Leave CPU time for camera capture and the Qt live preview.
            # Measure throughput again after this change; it is not a
            # guaranteed inference-speed improvement.
            cv2.setNumThreads(1)
            try:
                import torch
                torch.set_num_threads(2)
            except (ImportError, RuntimeError) as exc:
                log(f"CPU thread limit unavailable: {exc}")
            model = YOLO(str(model_path))''',
    "CPU thread allocation",
)

replace_once(
    '''                        class_name = tyre_class_name(
                            model.names.get(
                                int(class_id), "unknown"
                            )
                        )

                        if (''',
    '''                        class_name = tyre_class_name(
                            model.names.get(
                                int(class_id), "unknown"
                            )
                        )

                        # This model's eligible tyre classes are passenger
                        # and 4x4. Do not count another class.
                        if class_name not in ("passenger", "4x4"):
                            continue

                        if (''',
    "countable classes",
)

replace_once(
    '''                        changed = False
                        for line_index, ratio in enumerate((self.line_ratio,self.end_ratio)):''',
    '''                        # Weak boxes may help ByteTrack retain an ID, but
                        # must not establish a new side of a counting line.
                        if confidence < self.confidence:
                            continue

                        changed = False
                        for line_index, ratio in enumerate((self.line_ratio,self.end_ratio)):''',
    "confidence-gated crossing",
)

replace_once(
    '''                                    self.counted.emit(track_id,float(confidence))''',
    '''                                    self.counted.emit(
                                        track_id,
                                        float(confidence),
                                        self.processing_frame,
                                    )''',
    "crossing-frame signal emission",
)

replace_once(
    '''    def on_count(self, _track_id, _confidence):
        # Already committed to SQLite in CounterWorker.
        self.session += 1
        if self.worker is not None and self.worker.source_kind == "video":
            self.test_events.append(self.worker.processing_frame / max(1.0, self.worker.video_fps))''',
    '''    def on_count(self, _track_id, _confidence, crossing_frame):
        # Already committed to SQLite in CounterWorker.
        self.session += 1
        if self.worker is not None and self.worker.source_kind == "video":
            self.test_events.append(
                crossing_frame / max(1.0, self.worker.video_fps)
            )''',
    "video crossing timestamp",
)

replace_once(
    '''        flow = max((slot['count'] / max((slot['end'] - slot['start']).total_seconds() / 60, 1/60)
                    for slot in completed_slots), default=0.0)''',
    '''        def slot_minutes(slot):
            duration = slot["end"] - slot["start"]
            seconds = (
                duration.total_seconds()
                if isinstance(duration, timedelta)
                else float(duration)
            )
            return max(seconds / 60.0, 1.0 / 60.0)

        flow = max(
            (slot["count"] / slot_minutes(slot) for slot in completed_slots),
            default=0.0,
        )''',
    "video and live flow calculation",
)

# All expected changes must match before either file is written.
compile(edited, str(source), "exec")

backup = source.with_name(
    source.stem
    + "_backup_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + source.suffix
)
shutil.copy2(source, backup)

try:
    source.write_text(edited, encoding="utf-8")
except Exception:
    shutil.copy2(backup, source)
    raise

print(f"Edited: {source}")
print(f"Backup: {backup}")
print("Syntax check passed. Camera performance and tyre counts still need testing.")
