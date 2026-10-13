# TyreTrack V9.1 — Management access fix (TEST)

- Added a **MANAGEMENT** tab to the right-hand dashboard tabs.
- **OPEN MANAGEMENT PORTAL IN BROWSER** starts and opens the local stoppage reason editor.
- **REFRESH MANAGEMENT REASONS** displays incident times, durations, status, reasons, supervisors and comments inside TyreTrack (read-only).
- Only the local management portal edits reasons. The dashboard does not modify production counts, classifications, or incident timestamps.
- The **LEARNING** tab's original local portal control is preserved.
- The remote GitHub Pages portal (`docs/index.html`) is included but requires separate Supabase configuration and deployment. This new button opens the *local* portal, not the remote website.
- Tested with Python syntax compilation only; verify on a separate Windows test installation before production.
