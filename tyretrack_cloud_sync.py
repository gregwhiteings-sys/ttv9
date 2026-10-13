"""Optional outbound-only Supabase sync. Never modifies local counts."""
import configparser, json, sqlite3, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from hourly_dashboard import hourly_snapshot
from management_portal import sync_incidents

BRISBANE = timezone(timedelta(hours=10))
SOURCE = 'OAK-D S2 PoE / CAT5'

def settings(config_path):
    c = configparser.ConfigParser(); c.read(config_path, encoding='utf-8')
    if not c.has_section('supabase'): return None
    url=c.get('supabase','url',fallback='').strip().rstrip('/')
    key=c.get('supabase','service_role_key',fallback='').strip()
    site=c.get('supabase','site_id',fallback='brisbane-1').strip()
    if not url.startswith('https://') or not key: return None
    return url,key,site

def request(url,key,method,path,data=None):
    body=json.dumps(data).encode() if data is not None else None
    headers={'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json','Prefer':'resolution=merge-duplicates,return=minimal'}
    req=urllib.request.Request(url+'/rest/v1/'+path, data=body,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=12) as res: return res.read()

def publish(db,config_path,now=None):
    cfg=settings(config_path)
    if not cfg: return False
    url,key,site=cfg
    now=(now or datetime.now(BRISBANE)).astimezone(BRISBANE)
    shift=now.replace(hour=5,minute=0,second=0,microsecond=0)
    cutoff=shift.replace(hour=17,minute=5)
    sync_incidents(db,now)
    with sqlite3.connect(db,timeout=15) as con:
        rows=con.execute('SELECT metric_utc,tyre_type FROM counts WHERE source=? AND metric_utc>=? AND metric_utc<?', (SOURCE,shift.timestamp(),min(now,cutoff).timestamp())).fetchall()
        slots,best,_=hourly_snapshot(con,source=SOURCE,now=now)
        incidents=con.execute('SELECT incident_id,started,ended,duration_seconds,status FROM no_count_incidents WHERE started>=? ORDER BY started', (shift.isoformat(),)).fetchall()
    def tyre_kind(v):
        s=str(v or '').lower()
        if '4x4' in s or 'suv' in s: return 'suv'
        if 'passenger' in s: return 'passenger'
        return 'unknown'
    counts={'passenger':0,'suv':0,'unknown':0}
    for _,v in rows: counts[tyre_kind(v)]+=1
    recent=sum(1 for t,_ in rows if t is not None and t>=now.timestamp()-300)
    last=max((t for t,_ in rows if t is not None),default=None)
    status='OFF SHIFT' if now<shift or now>=cutoff else ('NO COUNT' if not last or now.timestamp()-last>=600 else 'RUNNING')
    stamp=now.isoformat(timespec='seconds')
    request(url,key,'POST','production_live?on_conflict=site_id',[dict(site_id=site,updated_at=stamp,shift_date=shift.date().isoformat(),total=len(rows),passenger=counts['passenger'],suv=counts['suv'],unknown=counts['unknown'],flow_per_minute=round(recent/5,2),status=status,best_hour_count=best['count'] if best else 0,best_hour_label=(best['start'].strftime('%H:%M')+'–'+best['end'].strftime('%H:%M')) if best else '')])
    hourly=[dict(site_id=site,shift_date=shift.date().isoformat(),slot=i['number'],start_at=i['start'].isoformat(),end_at=i['end'].isoformat(),count=i['count'],completed=i['completed']) for i in slots]
    request(url,key,'POST','production_hourly?on_conflict=site_id,shift_date,slot',hourly)
    if incidents:
        payload=[dict(site_id=site,incident_id=i,started=s,ended=e,duration_seconds=d,status=st) for i,s,e,d,st in incidents]
        request(url,key,'POST','production_incidents?on_conflict=site_id,incident_id',payload)
    # Pull manager explanations to the local DB; NEVER pull or modify production counts.
    raw=request(url,key,'GET','production_incidents?select=incident_id,reason,notes,submitted_by&site_id=eq.'+site+'&reason=not.is.null')
    records=json.loads(raw)
    with sqlite3.connect(db,timeout=15) as con:
        for r in records:
            iid=r.get('incident_id'); reason=r.get('reason')
            if not iid or not reason: continue
            existing=con.execute('SELECT reason,notes,submitted_by FROM management_reasons WHERE incident_id=? ORDER BY id DESC LIMIT 1',(iid,)).fetchone()
            vals=(reason,r.get('notes') or '',r.get('submitted_by') or 'Manager')
            if existing!=vals:
                con.execute('INSERT INTO management_reasons(created,incident_id,reason,notes,submitted_by) VALUES(?,?,?,?,?)',(stamp,iid,*vals))
    return True
