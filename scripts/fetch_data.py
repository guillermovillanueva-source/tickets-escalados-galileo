"""Baja los tickets escalados y genera docs/data.json.

- ClickUp: tareas de Customer Journey, Foundational Services y Reporte de
  Incidentes/Problemas Service Desk (Mesa de Ayuda Galileo), con su historial
  de estados.
- Slack: mensajes principales de #support-stream-aligned-teams desde el
  1 de enero de 2025; de ahí salen los ids de ClickUp que se escalaron.

Variables de entorno: CLICKUP_TOKEN (token personal, pk_...) y SLACK_TOKEN
(token de bot xoxb-... con channels:history, o groups:history si el canal es privado).
Solo usa la librería estándar de Python.
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

LISTS = ["901710352918", "901711164808", "901702215315"]
CHANNEL = "C015TG16HPH"
SLACK_OLDEST = "1735689600"  # 2025-01-01 00:00 UTC
TZ = dt.timezone(dt.timedelta(hours=-6))  # hora del centro de México
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "data.json")


def get(url, headers, tries=5):
    for i in range(tries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(int(e.headers.get("Retry-After", "10")) + 1)
                continue
            raise SystemExit(f"Error {e.code} en {url.split('?')[0]}: {e.read().decode('utf-8')[:300]}")
    raise SystemExit("Demasiados reintentos")


def iso(ms):
    if not ms:
        return None
    return dt.datetime.fromtimestamp(int(ms) / 1000, TZ).strftime("%Y-%m-%dT%H:%M")


def clickup(token):
    h = {"Authorization": token}
    tasks = []
    for lst in LISTS:
        page = 0
        while True:
            q = urllib.parse.urlencode({"include_closed": "true", "subtasks": "true", "page": page})
            r = get(f"https://api.clickup.com/api/v2/list/{lst}/task?{q}", h)
            tasks += r.get("tasks", [])
            if r.get("last_page", True) or not r.get("tasks"):
                break
            page += 1
    hist = {}
    ids = [t["id"] for t in tasks]
    for i in range(0, len(ids), 100):
        q = "&".join("task_ids=" + urllib.parse.quote(x) for x in ids[i:i + 100])
        hist.update(get(f"https://api.clickup.com/api/v2/task/bulk_time_in_status/task_ids?{q}", h))
    rows = []
    for t in tasks:
        sh = (hist.get(t["id"]) or {}).get("status_history") or []
        rev = next((s for s in sh if str(s.get("status", "")).lower() == "review"), None)
        closed = t.get("date_closed") or next((s.get("since") for s in sh if s.get("type") == "closed"), None)
        assignees = t.get("assignees") or []
        rows.append({
            "id": t["id"],
            "ticket": t.get("name"),
            "url": t.get("url"),
            "lista": (t.get("list") or {}).get("name", ""),
            "responsable": "; ".join(a.get("username") or "" for a in assignees) or "Sin asignar",
            "responsables_ids": ";".join(str(a["id"]) for a in assignees),
            "estado_clickup": (t.get("status") or {}).get("status"),
            "creado": iso(t.get("date_created")),
            "review": iso(rev.get("since")) if rev else None,
            "cerrado": iso(closed),
        })
    return rows


def slack(token):
    h = {"Authorization": "Bearer " + token}
    first = {}
    cursor = ""
    while True:
        q = {"channel": CHANNEL, "oldest": SLACK_OLDEST, "limit": 200}
        if cursor:
            q["cursor"] = cursor
        r = get("https://slack.com/api/conversations.history?" + urllib.parse.urlencode(q), h)
        if not r.get("ok"):
            raise SystemExit("Slack respondió: " + str(r.get("error")))
        for m in r.get("messages", []):
            fecha = dt.datetime.fromtimestamp(float(m["ts"]), TZ).strftime("%Y-%m-%dT%H:%M")
            for tid in set(re.findall(r"app\.clickup\.com/t/(?:\d+/)?([0-9a-z]+)", json.dumps(m))):
                if tid not in first or fecha < first[tid]:
                    first[tid] = fecha
        cursor = (r.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return [{"id": k, "fecha_canal": v} for k, v in first.items()]


def main():
    ck, sk = os.environ.get("CLICKUP_TOKEN"), os.environ.get("SLACK_TOKEN")
    if not ck or not sk:
        sys.exit("Faltan CLICKUP_TOKEN o SLACK_TOKEN")
    data = {
        "generado": dt.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M"),
        "tickets": clickup(ck),
        "canal": slack(sk),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"{len(data['tickets'])} tickets de ClickUp, {len(data['canal'])} ids en Slack")


if __name__ == "__main__":
    main()
