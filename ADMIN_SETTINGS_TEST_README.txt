TYRETRACK V9.2 — ADMIN SETTINGS TEST UPDATE

This is SOURCE CODE for a Windows portable build, not a compiled EXE.
Build using the existing BUILD_V5_COMPAT.py and your established Windows runtime.

Changes:
- STOP COUNTING requires administrator password and reason.
- Tray EXIT requires administrator password and reason.
- Clicking X hides the dashboard in the system tray; counting continues.
- Admin Settings button: edit low-flow alert threshold without rebuilding.
- Change administrator password using Admin Settings.
- Settings: data/private_config/operator_settings.json
- Password hash: data/private_config/admin_security.json
- Stop audit: data/admin_stop_history.csv (Brisbane timestamps)
- Initial temporary password: TyreTrack@2026!
- Change the temporary password on first launch.

IMPORTANT:
- This release DOES NOT yet provide editable camera resolution, FPS, email recipients,
  reporting schedules, or detector replacement through the Admin Settings UI.
- A Windows executable has not been built or tested here.
- Preserve the existing data folder and do not replace the working production app
  before OAK-D camera, counting, alerts, background operation and password tests.
- Windows Task Manager, Windows shutdown, and power failure are not protected by this password.
