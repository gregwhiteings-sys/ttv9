# TyreTrack V8 — linked stoppage reasons (TEST)

The management page now automatically lists no-count gaps of at least 10 minutes during the Brisbane 05:00–17:05 shift, including before the first tyre of the day. Each gap has a stable incident ID, start time, duration, open/closed status, and a reason form. Submitting a reason links it to that exact incident. Editing a reason adds an audit entry; existing tyre counts are never modified.

Open the **Learning** tab, start the **Management Page**, and open the local URL shown. Press **Refresh incidents** to see new events. The portal is bound to 127.0.0.1 only; access from phones requires a separately configured authenticated tunnel/VPN. Do not port-forward it publicly.

**Important:** The portal reconstructs gaps from OAK count timestamps. A gap can represent actual conveyor downtime *or* an AI detection/counting failure; the reason must be confirmed by management. It does not automatically distinguish these cases. A no-count event is shown after ten minutes even if the email alert was not sent (for example, camera offline). Historical incidents are not deleted by re-sync.

Use this as a separate TEST build, not a replacement for the working Australian installation. Verify the count-source value, alert timing, management submissions, and reports on Windows before deployment.
