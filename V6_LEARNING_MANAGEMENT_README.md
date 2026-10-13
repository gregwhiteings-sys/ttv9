# TyreTrack V6 – Learning Centre and Management Reasons (TEST BUILD)

## What is included
- New LEARNING tab with manual 20-second live OAK review clips. The app buffers approximately 10 seconds of recent frames at 6 FPS and saves approximately 10 seconds after a trigger. Saved under `data/learning_centre/<timestamp>/review.mp4` with `review.json`.
- Human review: select an incident, enter a verified tyre count and notes, save to `review.json`.
- Management stoppage reason webpage, launched from the LEARNING tab. It runs on `127.0.0.1:8765` (this PC only), with a per-launch secret URL token. Records reasons in the separate `management_reasons` SQLite table in the existing `data/tyretrack.db`.
- Existing detection weights, counting logic, classification, email schedules and V5 dashboard metrics are untouched.

## How to test
1. **Make a copy** of your V5 folder and back up its `data` folder. Do not replace the Australian production app.
2. Use the same Windows environment and dependencies as the V5 package. Keep `learning_centre.py` and `management_portal.py` alongside `TyreTrack_Production_Monitor.py` (or bundle them into the EXE).
3. Start live OAK counting, open **LEARNING**, press **SAVE 20-SECOND INCIDENT CLIP**. Wait 10 seconds, then **REFRESH SAVED INCIDENTS**. Select the clip and enter verified count and notes. No changes are made to the counting model.
4. Press **START LOCAL MANAGEMENT PAGE**. Copy the displayed URL into a browser **on the same PC**. Select reason, add notes and name, submit. The log is stored in the app database.
5. Review recorded clips and verify file sizes and disk space. Incident capture is deliberately sampled at 6 FPS and 640x360 to reduce overhead; it is not evidence of original full-resolution frame rate.

## Limitations / next stage
- **Automatic overlap triggers are not enabled yet.** Candidate overlap events require integration with detector/tracker metadata, not guessing from rendered bounding boxes. Manual event capture is implemented now.
- **No box drawing, YOLO label export, or automatic model training** yet. Human review notes/counts are stored; the next stage adds frame annotation and Colab export.
- Management reason form is **not yet linked automatically to a particular no-count alert**; operators can enter its time/ID. Future stage: incident selection and linkage.
- Phone access from outside the yard **is not exposed publicly**. Use an authenticated VPN and HTTPS reverse proxy for remote access, never public port-forwarding of 8765.
- The 20-second buffer is approximate, based on live GUI-delivered frames. If the GUI freezes or is overloaded, fewer frames may be captured.
- The app must remain open for the local management page to work. The secret link changes each launch.
- Not yet verified on Australian Windows 11 / OAK hardware. Test separately before production deployment.
