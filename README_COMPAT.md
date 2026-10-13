# TyreTrack V5 compatibility build

This is an **experimental Windows packaging repair**, not a verified executable. The app, detector and counting logic are unchanged.

Upload the ZIP contents to the root of your GitHub repository, including the hidden `.github/workflows/windows-v5-compat.yml` file. Then open GitHub Actions > TyreTrack V5 Compatibility Build > Run workflow.

The workflow pins torch 2.5.1+cpu and torchvision 0.20.1+cpu, creates and runs a minimal packaged PyTorch test first, then builds V5 with the old builder's `--collect-all torchvision` and `--collect-all depthai` strategy. It validates the segmentation detector and performs a 12-second startup check. On success download the portable artifact. On failure send the diagnostics artifact (especially `torch_probe_output.txt` or `startup_output.txt`). No old SQLite database or email secrets are included.

Do not overwrite your existing working application until you test this release on the Windows PC with recorded video, camera and reporting.
