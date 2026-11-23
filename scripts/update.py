#!/usr/bin/env python3
"""Best-effort schedule refresh. Never fabricates fixtures or TV listings."""
import datetime as dt
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/fixtures.json'
UTC=dt.timezone.utc
NOW=dt.datetime.now(UTC)

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'OlympiacosMatchCenter/1.0 (personal fixture display)','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=25) as res:
        return json.load(res)

def text(v):
    return str(v or '').strip()

def olympiacos(v):
    return bool(re.search(r'olympiac|olympiak|ολυμπιακ',text(v),re.I))

def iso(value):
    if not value:return None
    try:
        v=str(value).replace('Z','+00:00')
        d=dt.datetime.fromisoformat(v)
        if d.tzinfo is None:return None  # do not assume timezone
        return d.astimezone(UTC).isoformat().replace('+00:00','Z')
    except (ValueError,TypeError):return None

def add(out,sport,competition,home,away,start,source,identifier):
    if not (olympiacos(home) or olympiacos(away)):return
    t=iso(start)
    if not t:return
    when=dt.datetime.fromisoformat(t.replace('Z','+00:00'))
    if when<NOW-dt.timedelta(hours=4) or when>NOW+dt.timedelta(days=250):return
    out.append(dict(id=f'{sport}-{identifier}',sport=sport,competition=text(competition) or 'Competition not specified',home=text(home),away=text(away),start=t,channel=None,source_url=source))

def football(out,warnings):
    # ESPN schedule endpoint can change; fetch each competition independently.
    leagues={'gre.1':'Greek Super League','uefa.champions':'UEFA Champions League','uefa.europa':'UEFA Europa League','uefa.europa.conf':'UEFA Conference League'}
    total=0
    for code,label in leagues.items():
        url=f'https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/435/schedule'
        try:
            payload=fetch(url)
            for event in payload.get('events',[]):
                competitors=(event.get('competitions') or [{}])[0].get('competitors') or []
                if len(competitors)<2:continue
                home=next((c for c in competitors if c.get('homeAway')=='home'),competitors[0]);away=next((c for c in competitors if c.get('homeAway')=='away'),competitors[1])
                def name(c):return c.get('team',{}).get('displayName') or c.get('team',{}).get('name') or ''
                before=len(out)
                add(out,'football',label,name(home),name(away),event.get('date'),url,event.get('id','unknown'))
                total+=len(out)-before
        except Exception as e:warnings.append(f'Football {label} source unavailable: {type(e).__name__}')
    if not total:warnings.append('No upcoming football fixtures verified from configured feeds; Greek Cup may require an additional source.')

def basketball(out,warnings):
    url='https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games?limit=500'
    try:
        payload=fetch(url)
        games=payload.get('data',[]) if isinstance(payload,dict) else payload
        for g in games:
            if not isinstance(g,dict):continue
            # Feed versions vary: local/road and date keys are not uniform.
            def team(v):
                if isinstance(v,str):return v
                if not isinstance(v,dict):return ''
                return next((text(v.get(k)) for k in ('name','teamName','displayName','shortName','clubName') if v.get(k)), '')
            home=team(g.get('local') or g.get('home') or g.get('homeTeam'))
            away=team(g.get('road') or g.get('away') or g.get('awayTeam'))
            start=g.get('startDate') or g.get('date') or g.get('gameDate') or g.get('startTime') or g.get('utcDate')
            add(out,'basketball','EuroLeague',home,away,start,url,g.get('identifier') or g.get('gameCode') or g.get('id'))
    except Exception as e:warnings.append(f'EuroLeague source unavailable: {type(e).__name__}')
    # Domestic Greek Basket League / Greek Cup intentionally not fabricated.
    warnings.append('Greek basketball league/cup and Greek football cup require additional verified fixture feeds.')

def main():
    previous=json.loads(OUT.read_text()) if OUT.exists() else {'matches':[]}
    matches=[];warnings=[]
    football(matches,warnings);basketball(matches,warnings)
    overrides=json.loads((ROOT/'data/tv-overrides.json').read_text()).get('matches',{})
    for m in matches:
        key='|'.join([m['start'][:10],m['sport'],m['home'].lower(),m['away'].lower()])
        match_override=overrides.get(key,{})
        if isinstance(match_override,dict) and match_override.get('verified') is True:
            m['channel']=text(match_override.get('channel')) or None
    # Keep previously verified future fixtures if a source is temporarily unavailable.
    existing={m['id']:m for m in matches}
    for m in previous.get('matches',[]):
        if m.get('id') not in existing and m.get('start') and iso(m['start']):
            when=dt.datetime.fromisoformat(iso(m['start']).replace('Z','+00:00'))
            if NOW<=when<=NOW+dt.timedelta(days=250):existing[m['id']]=m
    result={'updated_at':NOW.isoformat().replace('+00:00','Z'),'matches':sorted(existing.values(),key=lambda m:m['start']),'warnings':warnings}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f"Stored {len(existing)} upcoming fixtures; {len(warnings)} feed notes")

if __name__=='__main__':main()
