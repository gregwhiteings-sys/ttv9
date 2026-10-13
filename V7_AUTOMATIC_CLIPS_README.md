# TyreTrack V7 — automatic review clips (TEST ONLY)

## Automatic triggers (live OAK only)
- 2+ detections in the previous inference frame become 1 (possible overlap).
- 2+ detections suddenly become 0 (unexpected disappearance).
- A tyre detection confidence below 0.40 (uncertain detection).

These are *suspected events*, not confirmed counting errors. A single overlap may not be detected, and a detection disappearing naturally at the image edge may trigger a false positive. Video-file playback never triggers capture.

## Video capture
- Rolling ~10 seconds before event + ~10 seconds afterward.
- Sampled at 6 FPS, 640x360, MP4. Clips may vary with actual frame availability.
- Saved in data/learning_centre/<timestamp>/review.mp4 and review.json.
- 90-second automatic trigger cooldown, one clip at a time, 1 GB free disk minimum.
- Manual Save Clip remains available.
- In Learning tab, click Refresh after ~10 seconds to see saved incidents.

## Safety
The detector weights, tyre counts, counting lines, emails, and management portal are unchanged. No automatic retraining. This is an unverified source-code test package, not a validated Windows executable. Back up data and test separately from production.
