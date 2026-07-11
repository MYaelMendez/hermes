"""Generate agentic-grid.html: a NVIDIA-Omniverse-tile spreadsheet dashboard.

Renders the bæsic ledger as a live spreadsheet grid (ticks x categories) plus
GPU + file-guard tiles, gold-on-void, sourced from the real chassis
(computer:// probe, file:// guard, C:\\ae\\ledger.csv). No Excel needed.
Open in VS Code via Simple Browser, or any browser.
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from hermes_cli.conductor import _dispatch  # noqa: E402


def gpu_probe() -> dict:
    try:
        r = _dispatch("computer:// probe")
        txt = r.get("surface", {}).get("probe") or ""
        for line in str(txt).splitlines():
            try:
                return json.loads(line)
            except Exception:
                continue
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}
    return {}


def ledger_rows() -> list[tuple[int, dict]]:
    path = r"C:\ae\ledger.csv"
    cats = ["01-Apps", "02-Media", "03-Projects", "04-Docs"]
    rows: dict[int, dict] = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                parts = line.strip().split(",")
                if len(parts) == 3 and parts[1] in cats:
                    try:
                        ts = int(parts[0]); val = int(parts[2])
                    except ValueError:
                        continue
                    rows.setdefault(ts, {c: 0 for c in cats})[parts[1]] = val
    return [(ts, rows[ts]) for ts in sorted(rows)]


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
    rows = ledger_rows()
    guard = file_guard()
    cats = ["01-Apps", "02-Media", "03-Projects", "04-Docs"]

    # spreadsheet grid: header + one row per tick
    head = "".join(f"<th>{c}</th>" for c in cats)
    body_rows = ""
    for ts, vals in rows:
        cells = "".join(f"<td>{vals[c]}</td>" for c in cats)
        body_rows += f"<tr><td class='ts'>{ts}</td>{cells}</tr>\n"
    # sparkline footer (last value per cat)
    spark = ""
    BARS = "▁▂▃▄▅▆▇█"
    for c in cats:
        series = [vals[c] for _, vals in rows]
        lo, hi = (min(series), max(series)) if series else (0, 0)
        span = hi - lo
        if series:
            line = "".join(BARS[int((v - lo) / span * 7)] if span else BARS[3] for v in series)
        else:
            line = ""
        spark += "<tr class='spark'><td class='ts'>" + c + "</td>" \
                 "<td colspan='" + str(len(cats)) + "' class='sparkline'>" \
                 + line + "  (" + str(lo) + "→" + str(hi) + ")</td></tr>\n"

    guard_rows = "\n".join(
        "<tr><td>" + label + "</td><td class='" + ("ok" if ok else "err") + "'>"
        + ("✓ " if ok else "✕ ") + verdict + "</td></tr>"
        for label, verdict, ok in guard
    )

    gpu_tiles = "".join(
        f"<div class='tile'><div class='k'>{k}</div><div class='v'>{v}</div></div>"
        for k, v in [
            ("GPU", gpu.get("name", "n/a")),
            ("VRAM total", f"{gpu.get('memory_total_mib',0)} MiB"),
            ("VRAM used", f"{gpu.get('memory_used_mib',0)} MiB"),
            ("Temp", f"{gpu.get('temperature_gpu',0)} °C"),
        ]
    )

    html = TEMPLATE.format(
        head=head, body_rows=body_rows, spark=spark,
        guard_rows=guard_rows, gpu_tiles=gpu_tiles,
        nticks=len(rows),
    )
    out = os.path.join(HERE, "agentic-grid.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", out, f"({len(rows)} ticks)")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>æ:// agentic-grid · Omniverse tiles · spreadsheet</title>
<style>
  :root {{
    --void:#050505; --gold:#D4AF37; --neon:#00ff9d; --ink:#f0ece4;
    --muted:rgba(240,236,228,0.4); --border:rgba(212,175,55,0.16);
    --border-hot:rgba(212,175,55,0.5); --panel:#090909; --panel-2:#0b0b0b;
    --glow:rgba(212,175,55,0.08);
  }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; background:var(--void); color:var(--ink);
    font-family:'JetBrains Mono',ui-monospace,Menlo,monospace; }}
  body::before {{ content:""; position:fixed; inset:0; pointer-events:none; z-index:9999;
    opacity:0.035; background:repeating-linear-gradient(0deg,transparent,transparent 2px,
    rgba(212,175,55,0.12) 2px,rgba(212,175,55,0.12) 4px); }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:26px 20px 60px; }}
  .brand {{ display:flex; gap:14px; align-items:center; margin-bottom:18px; }}
  .glyph {{ width:46px; height:46px; border:1px solid var(--border-hot); display:grid;
    place-items:center; color:var(--gold); font-weight:800; font-size:24px;
    box-shadow:0 0 18px var(--glow); }}
  .title {{ font-family:'Orbitron',sans-serif; color:var(--gold); font-weight:700;
    letter-spacing:0.1em; font-size:20px; }}
  .sub {{ color:var(--muted); font-size:11px; letter-spacing:0.16em; text-transform:uppercase; }}
  .panel {{ border:1px solid var(--border); background:var(--panel); padding:16px; margin-bottom:18px; }}
  .panel-head {{ color:var(--gold); font-weight:700; letter-spacing:0.14em; text-transform:uppercase;
    font-size:11px; margin-bottom:12px; display:flex; justify-content:space-between; }}
  .panel-head .sub {{ color:var(--muted); text-transform:none; letter-spacing:0; }}

  /* NVIDIA Omniverse tile grid */
  .tiles {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
  @media(max-width:760px){{ .tiles{{grid-template-columns:repeat(2,1fr);}} }}
  .tile {{ border:1px solid var(--border); background:var(--panel-2); padding:12px; min-height:64px; }}
  .tile .k {{ color:var(--muted); font-size:10px; letter-spacing:0.14em; text-transform:uppercase; }}
  .tile .v {{ color:var(--neon); font-family:'Orbitron',sans-serif; font-size:15px; margin-top:6px;
    word-break:break-word; }}

  /* spreadsheet */
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ border:1px solid var(--border); padding:8px 10px; text-align:right; }}
  th {{ color:var(--gold); letter-spacing:0.1em; text-transform:uppercase; font-size:10px;
    background:var(--panel-2); }}
  td.ts {{ color:var(--muted); text-align:left; font-size:11px; }}
  tbody tr:hover {{ background:var(--panel-2); }}
  tr.spark td {{ background:var(--panel-2); }}
  .sparkline {{ color:var(--gold); letter-spacing:2px; text-align:left; font-size:14px; }}
  .ok {{ color:#7ee787; }} .err {{ color:#ff7b72; }}
  .foot {{ color:var(--muted); font-size:10px; letter-spacing:0.12em; margin-top:22px;
    text-align:center; text-transform:uppercase; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <div class="glyph">æ</div>
    <div>
      <div class="title">agentic-grid</div>
      <div class="sub">NVIDIA Omniverse tiles · sovereign spreadsheet · +bæsic://</div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-head"><span>Agentic computer · Victus GPU-MCP</span>
      <span class="sub">computer:// probe</span></div>
    <div class="tiles">
{gpu_tiles}
    </div>
  </div>

  <div class="panel">
    <div class="panel-head"><span>Ledger spreadsheet (bæsic · in-language counts)</span>
      <span class="sub">{nticks} ticks · source C:\\ae\\ledger.csv</span></div>
    <table>
      <thead><tr><th>tick</th>{head}</tr></thead>
      <tbody>
{body_rows}{spark}
      </tbody>
    </table>
  </div>

  <div class="panel">
    <div class="panel-head"><span>file:// guard</span>
      <span class="sub">count &gt; mutate · sovereign-scoped</span></div>
    <table>
      <thead><tr><th>action</th><th>verdict</th></tr></thead>
      <tbody>
{guard_rows}
      </tbody>
    </table>
  </div>

  <div class="foot">#opensourceware #250 · +æ^victus · no Excel required</div>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
