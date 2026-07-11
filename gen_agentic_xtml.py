"""Generate agentic.xtml with LIVE chassis-sourced data (the proof, not prose).

Pulls real values from the conductor (computer:// probe GPU telemetry,
file:// sovereign guard, bæsic ledger counts) and injects them into the
gold-on-void agentic-language-chassis template. Run from C:\\ae\\hermes-fork.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from hermes_cli.conductor import _dispatch  # noqa: E402


def gpu_probe() -> dict:
    try:
        r = _dispatch("computer:// probe")
        txt = r.get("surface", {}).get("probe") or ""
        import json
        for line in str(txt).splitlines():
            try:
                return json.loads(line)
            except Exception:
                continue
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}
    return {}


def ledger_counts() -> list[tuple[str, int]]:
    path = r"C:\ae\ledger.csv"
    cats = ["01-Apps", "02-Media", "03-Projects", "04-Docs"]
    last = {c: 0 for c in cats}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                parts = line.strip().split(",")
                if len(parts) == 3 and parts[1] in last:
                    try:
                        last[parts[1]] = int(parts[2])
                    except ValueError:
                        pass
    return [(c, last[c]) for c in cats]


def file_guard() -> list[tuple[str, str, bool]]:
    q = [
        ("file:// count C:/æ/hermes-fork", "count sovereign root"),
        ("file:// move C:/æ/hermes-fork/x C:/Users/yaelm/OneDrive/y", "mutate off-root"),
        ("file:// enumerate C:/Users/yaelm/OneDrive", "reach OneDrive"),
    ]
    out = []
    for query, label in q:
        r = _dispatch(query)
        out.append((label, "ALLOWED" if r["ok"] else "DENIED", r["ok"]))
    return out


def main() -> None:
    gpu = gpu_probe()
    counts = ledger_counts()
    guard = file_guard()

    gpu_name = gpu.get("name", "unknown")
    gpu_total = gpu.get("memory_total_mib", 0)
    gpu_temp = gpu.get("temperature_gpu", 0)
    gpu_used = gpu.get("memory_used_mib", 0)

    cards = "\n".join(
        f'      <div class="card"><div class="cat">{c}</div>'
        f'<div class="num">{n}</div><div class="bar">'
        f'<span style="width:{min(100, n*6)}%"></span></div></div>'
        for c, n in counts
    )
    guard_rows = "\n".join(
        f'      <div class="grow"><span class="{"ok" if ok else "err"}">'
        f'{"✓" if ok else "✕"}</span> {label} &rarr; {verdict}</div>'
        for label, verdict, ok in guard
    )

    html = TEMPLATE.format(
        gpu_name=gpu_name, gpu_total=gpu_total, gpu_temp=gpu_temp,
        gpu_used=gpu_used, cards=cards, guard_rows=guard_rows,
        epoch=int(os.path.getmtime(r"C:\ae\ledger.csv")) if os.path.exists(r"C:\ae\ledger.csv") else 0,
    )
    out = os.path.join(HERE, "agentic.xtml")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", out)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>æ:// — agentic.xtml · the chassis is always a language</title>
<style>
  :root {{
    --void:#050505; --gold:#D4AF37; --neon:#00ff9d; --ink:#f0ece4;
    --muted:rgba(240,236,228,0.4); --border:rgba(212,175,55,0.16);
    --border-hot:rgba(212,175,55,0.5); --panel:#090909; --panel-2:#0b0b0b;
    --glow:rgba(212,175,55,0.08);
  }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; background:var(--void); color:var(--ink);
    font-family:'JetBrains Mono',ui-monospace,Menlo,monospace; min-height:100vh; }}
  body::before {{ content:""; position:fixed; inset:0; pointer-events:none; z-index:9999;
    opacity:0.035; background:repeating-linear-gradient(0deg,transparent,transparent 2px,
    rgba(212,175,55,0.12) 2px,rgba(212,175,55,0.12) 4px); }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:28px 22px 60px; }}
  .brand {{ display:flex; gap:14px; align-items:center; margin-bottom:6px; }}
  .glyph {{ width:46px; height:46px; border:1px solid var(--border-hot); display:grid;
    place-items:center; color:var(--gold); font-weight:800; font-size:24px;
    box-shadow:0 0 18px var(--glow); }}
  .title {{ font-family:'Orbitron',sans-serif; color:var(--gold); font-weight:700;
    letter-spacing:0.1em; font-size:20px; }}
  .sub {{ color:var(--muted); font-size:11px; letter-spacing:0.16em; text-transform:uppercase; }}
  .lede {{ color:var(--ink); font-size:14px; line-height:1.7; margin:22px 0 30px;
    border-left:2px solid var(--border-hot); padding-left:16px; }}
  .lede b {{ color:var(--gold); }}
  .panel {{ border:1px solid var(--border); background:var(--panel); padding:18px; margin-bottom:18px; }}
  .panel-head {{ color:var(--gold); font-weight:700; letter-spacing:0.14em; text-transform:uppercase;
    font-size:11px; margin-bottom:14px; display:flex; justify-content:space-between; }}
  .panel-head .sub {{ color:var(--muted); text-transform:none; letter-spacing:0; }}
  .cards {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }}
  @media(max-width:640px){{ .cards{{grid-template-columns:1fr;}} }}
  .card {{ border:1px solid var(--border); background:var(--panel-2); padding:14px; }}
  .card .cat {{ color:var(--muted); font-size:11px; letter-spacing:0.14em; text-transform:uppercase; }}
  .card .num {{ color:var(--gold); font-family:'Orbitron',sans-serif; font-size:34px;
    text-shadow:0 0 16px var(--glow); margin:4px 0 10px; }}
  .card .bar {{ height:6px; background:#0a0a0a; border:1px solid var(--border); }}
  .card .bar span {{ display:block; height:100%; background:var(--gold);
    box-shadow:0 0 10px var(--glow); }}
  .gpu {{ display:flex; gap:22px; flex-wrap:wrap; }}
  .gpu .stat {{ }}
  .gpu .k {{ color:var(--muted); font-size:10px; letter-spacing:0.14em; text-transform:uppercase; }}
  .gpu .v {{ color:var(--neon); font-family:'Orbitron',sans-serif; font-size:22px; }}
  .grow {{ display:flex; flex-direction:column; gap:8px; }}
  .grow > div {{ font-size:13px; }}
  .ok {{ color:#7ee787; }} .err {{ color:#ff7b72; }}
  .thesis {{ color:var(--muted); font-size:12px; line-height:1.8; }}
  .thesis b {{ color:var(--gold); }}
  .foot {{ color:var(--muted); font-size:10px; letter-spacing:0.12em; margin-top:24px;
    text-align:center; text-transform:uppercase; }}
  kbd {{ background:var(--panel-2); border:1px solid var(--border); color:var(--muted);
    padding:2px 6px; font-size:10px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <div class="glyph">æ</div>
    <div>
      <div class="title">agentic.xtml</div>
      <div class="sub">the chassis is always a language · +bæsic:// · +æ^victus</div>
    </div>
  </div>

  <div class="lede">
    Conventional file management is <b>imperative and forgetful</b> &mdash; it acts first and
    records nothing. When your 15 desktop files vanished into OneDrive's recycle, there was no
    trail. <b>bæsic + mech on the chassis flip that</b>: the calculation lives in-language, the
    drift shows as a number, and mutation is denied by default. This page is rendered from
    <b>live chassis data</b> &mdash; not hardcoded.
  </div>

  <div class="panel">
    <div class="panel-head"><span>Live desktop ledger (bæsic · in-language counts)</span>
      <span class="sub">source: C:\\ae\\ledger.csv</span></div>
    <div class="cards">
{cards}
    </div>
  </div>

  <div class="panel">
    <div class="panel-head"><span>Agentic computer on Victus GPU-MCP</span>
      <span class="sub">computer:// probe &rarr; real GPU-MCP subprocess</span></div>
    <div class="gpu">
      <div class="stat"><div class="k">GPU</div><div class="v">{gpu_name}</div></div>
      <div class="stat"><div class="k">VRAM total</div><div class="v">{gpu_total} MiB</div></div>
      <div class="stat"><div class="k">VRAM used</div><div class="v">{gpu_used} MiB</div></div>
      <div class="stat"><div class="k">Temp</div><div class="v">{gpu_temp}&deg;C</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-head"><span>file:// guard (count &gt; mutate, sovereign-scoped)</span>
      <span class="sub">the firewall that stops the next data-loss</span></div>
    <div class="grow">
{guard_rows}
    </div>
  </div>

  <div class="panel">
    <div class="panel-head"><span>Thesis</span><span class="sub">why better than conventional</span></div>
    <div class="thesis">
      <b>Count &gt; mutate.</b> file:// is read-default and clamped to C:\\ae; move is denied;
      OneDrive paths are denied.<br/>
      <b>Calc in-language.</b> the bæsic ledger persists <kbd>epoch,cat,count</kbd> and graphs
      deltas as sparklines &mdash; drift is a number, not a mystery.<br/>
      <b>mech is the grammar.</b> count &rArr; delta &rArr; graph as reactive dataflow; bæsic
      carries it today (mech compiler pending).<br/>
      <b>One language, one truth.</b> file:// reads the same sovereign root the ledger writes.
      They cannot disagree.
    </div>
  </div>

  <div class="foot">#opensourceware #250 · +æ^victus · rendered {epoch}</div>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
