TyreTrack V9.2 Sound Alerts - Windows GitHub build source
Includes fixed recorded-video flow parsing (0.0 tyres/min), low-flow Australian voice,
BEST HOUR cheering then Australian voice, and existing admin security settings.
Sounds are editable outside the executable in sounds/:
  low_flow_voice.wav
  best_hour_cheer.wav
  best_hour_voice.wav
Use uncompressed PCM WAV for replacement.
The Windows builder copies sounds/ to the portable release beside the EXE.
The speech volume setting currently does not change WAV playback loudness; adjust
Windows volume or edit WAV files to change their volume.
The BEST HOUR celebration is based on a new best COMPLETED hour.
TEST BUILD ONLY. GitHub Actions and live OAK-D have not yet been run/verified.
Keep existing production installation intact until validation.
