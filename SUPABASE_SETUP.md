# TyreTrack V9 — GitHub Pages + Supabase (TEST)

## 1. Supabase
1. Create a Supabase project. In SQL Editor run `supabase_schema.sql` once. If rerunning, pre-existing policies may cause errors; do not ignore SQL errors.
2. Under Authentication, create/invite each manager, confirm their email, and assign their auth UUID to site `brisbane-1` with `insert into public.manager_sites(user_id,site_id) values ('AUTH-USER-UUID','brisbane-1');`.
3. Keep the **service_role key secret**. It belongs **only** on the Australian PC, never in GitHub, browser, or public website. The browser uses the **anon/publishable key**.
4. The site permission uses Supabase RLS and column-level UPDATE grants. Managers can SELECT production tables and UPDATE only `reason`, `notes`, `submitted_by` on incidents. They cannot INSERT or DELETE records or edit count/timing fields.

## 2. Australian PC
Create `supabase_config.ini` alongside your existing private `email_config.ini` (the app uses `PRIVATE_CONFIG_DIR`) with:

```ini
[supabase]
url = https://YOUR-PROJECT.supabase.co
service_role_key = YOUR-SECRET-SERVICE-ROLE-KEY
site_id = brisbane-1
```

Keep the file out of Git and backups accessible to managers. The app attempts outbound sync every 60 seconds **only during a live OAK session**; it never syncs during recorded-video testing. A failure is logged, and production counting continues. Cloud sync uses HTTPS; no inbound port forwarding is needed. It uploads today's shift totals and hourly slots, incident status/timing, and downloads management reason updates into the local incident log. Cloud data is not the counting source of truth.

**Note:** this is a first test integration. If internet connectivity fails, the portal displays a stale timestamp; it does not queue every historical shift for backfill. Do not treat remote data as final until reconciled against the local database.

## 3. GitHub Pages
Publish the `docs/` folder from your GitHub repository's main branch in Settings → Pages. Open the resulting Pages address. Enter the Supabase project URL and **anon/publishable** key on the connection form, then sign in as an authorised manager. These settings are kept only in the current page session; refresh requires re-entering them.

## 4. Test checklist
- Test manager can read current live totals, passenger/SUV, hourly slots and incident status.
- Confirm the page shows **STALE** when uploads stop for more than 3 minutes.
- Test supervisor can save a stoppage reason, and that it appears in the local incident database on the next successful sync.
- Test authenticated manager PATCH to `production_live.total` and `production_incidents.duration_seconds` is rejected (403); no change in database.
- Test unauthenticated access and unassigned user access are rejected.
- Test OAK live versus recorded-video: video tests must never publish production data.
- Do not install on the production PC until the full Windows/OAK and security tests pass.

## Important
The local V8 management portal remains included. GitHub Pages cannot directly read the PC's SQLite database; Supabase is the intermediate service. This ZIP does **not** create your Supabase project or deploy your GitHub Pages site; those require your account credentials.
