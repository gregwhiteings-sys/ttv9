# TyreTrack V9.1 Windows portable build

This package is SOURCE, not a precompiled EXE. Build on GitHub-hosted Windows 11 with Python 3.12.

1. Create a PRIVATE GitHub repository. Upload all contents of this ZIP into its root, including the hidden `.github/workflows` folder. Never commit email passwords or Supabase service-role keys.
2. In GitHub Actions select **TyreTrack V9.1 Windows Portable Build** and **Run workflow**.
3. Download the artifact **TyreTrack-V9-1-Compat-Windows-Portable** after a successful run. Extract ALL files and launch TyreTrack.exe from its own folder.
4. Keep your existing working production directory untouched. Test video first, then live OAK-D, management tab, incident recording, management portal, and email before deployment.
5. The remote management phone website still requires Supabase/GitHub Pages configuration; packaging does not deploy it.

The build script explicitly includes the V9.1 Learning Centre, local management portal and cloud-sync modules. GitHub Actions checks source compilation and the packaged startup. Hardware and live email require on-site validation.

**Note:** If the build fails, download the Diagnostics artifact and share the logs.
