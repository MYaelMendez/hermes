#!/usr/bin/env python3
"""qc64_basic.py - +æ:// language conventions on a qc64 BASIC chassis.

Chassis: dakk/qc64 (MIT) - pure line-numbered BASIC, gosub dispatch table.
We reuse its shape (line numbers, rem comments, gosub routes, input loop)
as the reference interpreter for +æ:// scheme routing. The dispatch table
is NOT faked: it is loaded from hermes_cli.conductor's real registered
schemes, so the BASIC program below literally walks the live router.

Run:  PYTHONPATH=. python qc64_basic.py
      > +æ://glocal-agent
      > viewport://hermes-agent
      > æ://glocal-agent home://
      > exit

Fidelity note: this is a faithful *chassis* (line numbers + gosub table +
rem docstrings), not a full Commodore BASIC. WHILE/WEND, arrays, and the
PETSCII print codes are stubbed where the chassis does not need them.
The point is the routing grammar, which is exact: longest-prefix wins,
same as conductor._DISPATCHER.
"""
from __future__ import annotations
import os
import re
import sys
from hermes_cli.conductor import _DISPATCHER


# ---- the BASIC program (line-numbered; mirrors qc64's structure) ----
PROGRAM = r"""
05 rem +ae:// chassis - load live scheme routes from conductor
10 gosub 900
20 print "ae:// runtime ready - "; routes$; " schemes registered"
30 print "enter a scheme (exit to quit):"
40 input s$
50 if s$ = "exit" then goto 1000
60 gosub 800
70 goto 40
1000 print "halt."
1090 end

800 rem dispatch - longest prefix wins (same as conductor)
810 best$ = "" : bp = 0
820 for i = 1 to nroutes
830   p$ = prefix$(i)
840   if left$(s$, len(p$)) = p$ and len(p$) > bp then best$ = p$ : bp = len(p$)
850 next i
860 if bp = 0 then print "unsupported scheme: "; s$ : return
870 print "route ["; best$; "] -> resolved"
880 rem (matched route described inline above)
882 return

900 rem load real routes from hermes_cli.conductor._DISPATCHER
910 nroutes = 0
920 plist$ = str$(0)
930 nroutes = count_routes()
940 plist$ = get_routes()
950 for i = 1 to nroutes
960   prefix$(i) = route_at$(i)
970 next i
980 routes$ = str$(nroutes)
990 return
"""


class BasicVM:
    """Minimal line-numbered BASIC interpreter matching qc64's grammar
    (gosub/return, goto, if/then, for/next, print, input, left$, rem)."""

    def __init__(self, src: str):
        self.lines: dict[int, str] = {}
        for raw in src.strip().splitlines():
            raw = raw.rstrip()
            if not raw.strip():
                continue
            # split "10 print x" -> (10, "print x")
            sp = raw.split(None, 1)
            try:
                ln = int(sp[0])
            except ValueError:
                continue
            self.lines[ln] = sp[1] if len(sp) > 1 else ""
        self.vars: dict[str, object] = {}
        self.arr: dict[str, dict[int, object]] = {}  # NAME$(idx) string arrays
        self.stack: list[int] = []
        self.pc = min(self.lines)
        self.routes: list[str] = []
        self._halt = False
        # expose helpers to the program via pseudo-vars
        self.vars["_DISPATCHER"] = _DISPATCHER

    # --- string array support: prefix$(i) ---
    def _arr_get(self, name: str, idx: int):
        name = name.rstrip("$")
        return self.arr.get(name, {}).get(idx, "")

    def _arr_set(self, name: str, idx: int, val):
        name = name.rstrip("$")
        self.arr.setdefault(name, {})[idx] = val

    def run(self):
        trace = os.environ.get("QC64_TRACE") == "1"
        while self.pc is not None and self.pc in self.lines and not self._halt:
            stmt = self.lines[self.pc]
            nxt = self._next_line(self.pc)
            if trace:
                import sys; sys.stderr.write(f"[pc={self.pc}] {stmt}\n")
            self.exec_line(stmt)
            if self.pc == self._exec_pc_at:
                self.pc = nxt
            else:
                self.pc = self._exec_pc_at

    def _next_line(self, ln: int) -> int | None:
        keys = [k for k in self.lines if k > ln]
        return min(keys) if keys else None

    def exec_line(self, stmt: str):
        trace = os.environ.get("QC64_TRACE") == "1"
        self._exec_pc_at = self.pc
        s = stmt.strip()
        # strip inline ` ; comment` (BASIC REM-style trailing comment)
        if " ;" in s and not (s.startswith('"') and s.endswith('"')):
            s = s.split(" ;", 1)[0].strip()
        if not s or s.lower().startswith("rem"):
            return
        # statement chaining with ':' (Commodore BASIC)
        # NOTE: do NOT split `if` lines - their `then ... : ...` clause is
        # handled internally by the if-handler's recursion, and splitting would
        # execute `: return` / `: bp=...` unconditionally (outside the clause).
        if (":" in s and not (s.startswith('"') and s.endswith('"'))) and not s.lower().startswith("if "):
            parts, buf, q = [], "", False
            for ch in s:
                if ch == '"':
                    q = not q
                if ch == ":" and not q:
                    parts.append(buf); buf = ""
                else:
                    buf += ch
            if buf.strip():
                parts.append(buf)
            # only treat as chained statements if a real outside-':' split happened
            if len(parts) > 1:
                for p in parts:
                    p = p.strip()
                    if p:
                        self.exec_line(p)
                return
        # for/next
        if s.lower().startswith("for "):
            if getattr(self, "_active_for", None) == self.pc:
                # re-entry from next: skip re-init, fall through to body
                self._exec_pc_at = self.pc
                return
            body = s[4:]
            name, rest = body.split("=", 1)
            lo, hi = rest.split("to")
            self.vars[name.strip()] = int(self.eval_expr(lo))
            self._exec_pc_at = self.pc
            self._for_hi = int(self.eval_expr(hi))
            self._for_var = name.strip()
            self._for_line = self.pc
            self._active_for = self.pc
            return
        if s.lower().startswith("next"):
            v = self._for_var
            self.vars[v] += 1
            if trace:
                import sys; sys.stderr.write(f"  next: {v}={self.vars[v]} hi={self._for_hi} line={self._for_line}\n")
            if self.vars[v] <= self._for_hi:
                self._exec_pc_at = self._for_line
            else:
                self._active_for = None
                self._exec_pc_at = self._next_line(self.pc)
            return
        # goto
        if s.lower().startswith("goto "):
            self._exec_pc_at = int(s[5:].strip())
            return
        # gosub / return
        if s.lower().startswith("gosub "):
            self.stack.append(self._next_line(self.pc))
            self._exec_pc_at = int(s[6:].strip())
            return
        if s.lower().startswith("return"):
            self._exec_pc_at = self.stack.pop()
            return
        # if/then
        if s.lower().startswith("if "):
            cond, then = s[3:].partition(" then ")[0], s[3:].partition(" then ")[2]
            if self.eval_bool(cond.strip()):
                self.exec_line(then.strip())
            return
        # input
        if s.lower().startswith("input "):
            target = s[6:].strip()
            key = target[:-1] if target.endswith("$") else target
            try:
                self.vars[key] = input("> ").strip()
            except EOFError:
                self.vars[key] = "exit"
            return
        # print
        if s.lower().startswith("print "):
            self.basic_print(s[6:].strip())
            return
        if "=" in s and not s.lower().startswith(("print", "input", "goto", "gosub", "if", "for", "next", "return")):
            self.assignment(s)
            return
        # bare call to a gosub label like "gosub 900" already handled
        if s.lower().startswith("end"):
            self.pc = None
            self._exec_pc_at = None
            self._halt = True

    def _find_for(self, pc: int):
        # walk backwards to the matching FOR
        keys = [k for k in self.lines if k < pc]
        for k in reversed(keys):
            if self.lines[k].lower().startswith("for "):
                return k
        return pc

    def assignment(self, s: str):
        name, val = s.split("=", 1)
        name = name.strip()
        if "$(" in name:
            # array element: prefix$(i) = ...
            base = name.split("$(")[0].rstrip("$")
            idx = int(self.eval_expr(name.split("(", 1)[1].rstrip(")")))
            self._arr_set(base, idx, str(self.eval_expr(val)))
        elif name.endswith("$"):
            nm = name[:-1]
            self.vars[nm] = str(self.eval_expr(val))
        else:
            self.vars[name] = self.eval_expr(val)

    def basic_print(self, expr: str):
        out = []
        for part in self._split_print(expr):
            part = part.strip()
            if part.startswith('"') and part.endswith('"'):
                out.append(part[1:-1])
            else:
                v = self.eval_expr(part)
                out.append(str(v))
        print("".join(out))

    def _split_print(self, expr: str):
        # naive split on ; (qc64 uses ; to concatenate)
        return expr.split(";")

    def eval_bool(self, e: str) -> bool:
        e = e.strip()
        # chained AND
        if " and " in e.lower():
            return all(self.eval_bool(p) for p in re.split(r"\s+and\s+", e, flags=re.I))
        if " or " in e.lower():
            return any(self.eval_bool(p) for p in re.split(r"\s+or\s+", e, flags=re.I))
        # comparison: a OP b   (OP in = < > <= >= <>)
        m = re.match(r"^(.*?)\s*(<=|>=|<>|!=|=|<|>)\s*(.*)$", e, re.S)
        if not m:
            # bare expression truthiness
            v = self.eval_expr(e)
            return bool(v) and v != 0 and v != ""
        a_raw, op, b_raw = m.group(1).strip(), m.group(2), m.group(3).strip()
        a = self.eval_expr(a_raw)
        b = self.eval_expr(b_raw)
        # numeric compare if both numeric
        try:
            af, bf = float(a), float(b)
            if op == "=" or op == "<>":  # BASIC <> is not-equal; = is equal
                return af == bf if op == "=" else af != bf
            if op == "!=":
                return af != bf
            if op == "<":
                return af < bf
            if op == ">":
                return af > bf
            if op == "<=":
                return af <= bf
            if op == ">=":
                return af >= bf
        except (ValueError, TypeError):
            pass
        # string compare
        a, b = str(a), str(b)
        if op == "=":
            return a == b
        if op == "<>":
            return a != b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        return False

    def eval_expr(self, e: str):
        e = e.strip()
        if e == "":
            return ""
        if e.startswith('"') and e.endswith('"'):
            return e[1:-1]
        if e == "nroutes":
            return self.vars.get("nroutes", 0)
        if e == "routes$":
            return str(self.vars.get("nroutes", 0))
        if e == "_DISPATCHER":
            return _DISPATCHER
        # len$(x) / len(x)
        if e.lower().startswith("len("):
            inner = e[4:].rstrip(")")
            return len(str(self.eval_expr(inner)))
        # str$(x)
        if e.lower().startswith("str$("):
            inner = e[5:].rstrip(")")
            return str(self.eval_expr(inner))
        # left$(s$, n)
        if e.lower().startswith("left$("):
            inner = e[6:].rstrip(")")
            s_part, n_part = inner.split(",", 1)
            s_val = self._resolve_str(s_part.strip())
            n_val = int(self.eval_expr(n_part))
            return s_val[:n_val]
        # chassis helpers (vm._helpers) - checked BEFORE generic array branch
        if getattr(self, "_helpers", None):
            if e == "count_routes()":
                return self._helpers["count_routes"]()
            if e == "get_routes()":
                return self._helpers["get_routes"]()
            if e.startswith("route_at$("):
                idx = int(self.eval_expr(e[len("route_at$("):-1]))
                return self._helpers["route_at$"](idx)
            # ledger / filesystem helpers: NAME$(args) or NAME(args)
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\$?\(\s*(.*?)\s*\)$", e)
            if m:
                fn, arg = m.group(1), m.group(2).strip()
                # try exact (NAME), then NAME$ (string-returning)
                if fn in self._helpers:
                    if fn == "cat":  # cat$ joins raw parts itself
                        return self._helpers[fn](arg)
                    return self._helpers[fn](self.eval_expr(arg))
                if (fn + "$") in self._helpers:
                    if fn == "cat":  # cat$ joins raw parts itself
                        return self._helpers[fn + "$"](arg)
                    return self._helpers[fn + "$"](self.eval_expr(arg))
        # prefix$(i) -> string array element
        if e.endswith(")") and "$(" in e and not e.startswith("_DISPATCHER"):
            base = e.split("$(")[0].rstrip("$")
            idx = int(self.eval_expr(e.split("(", 1)[1].rstrip(")")))
            return self._arr_get(base, idx)
        # _DISPATCHER.prefixes() -> live registered routes
        if e == "_DISPATCHER.prefixes()":
            return [p for p, _ in _DISPATCHER._handlers]
        # bare string vars (s$, best$, p$, routes$, etc.)
        if e.endswith("$") and not "(" in e:
            return self._resolve_str(e)
        if e in self.vars:
            return self.vars[e]
        try:
            return int(e)
        except ValueError:
            try:
                return float(e)
            except ValueError:
                return e

    def _resolve_str(self, name: str):
        name = name.strip()
        if name.endswith("$") and not "(" in name:
            base = name[:-1]
            if base in self.vars:
                return str(self.vars[base])
            if name in self.vars:
                return str(self.vars[name])
            return ""
        if name == "s$":
            return str(self.vars.get("s", ""))
        return name


def _count_items(path: str) -> str:
    """Count ALL entries (dirs + files, non-recursive) in a directory."""
    try:
        return str(sum(1 for _ in __import__("os").scandir(path)))
    except OSError:
        return "0"


def _count_items(path: str) -> str:
    """Count ALL entries (dirs + files, non-recursive) in a directory."""
    try:
        return str(sum(1 for _ in __import__("os").scandir(path)))
    except OSError:
        return "0"


def _ledger_append(arg: str):
    """BASIC helper payload: 'path|text' -> append text as one line to path."""
    path, _, text = arg.partition("|")
    path = path.strip()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text + "\n")
    return "1"


def _spark_for(arg: str) -> str:
    """Return a unicode sparkline of a category's count history.
    arg = 'path;cat' (ledger.csv path ; category name)."""
    path, _, cat = arg.partition("|")
    path = path.strip()
    if not os.path.exists(path):
        return ""
    series = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) == 3 and parts[1] == cat:
                try:
                    series.append(int(parts[2]))
                except ValueError:
                    pass
    if not series:
        return ""
    bars = "▁▂▃▄▅▆▇█"
    lo, hi = min(series), max(series)
    span = hi - lo
    out = []
    for v in series:
        if span == 0:
            out.append("▄")
        else:
            idx = int((v - lo) / span * (len(bars) - 1))
            out.append(bars[idx])
    return "".join(out) + f"  ({lo}→{hi})"


def _ledger_read(arg: str):
    """BASIC helper payload: path -> '\n'-joined lines (for graphing in BASIC)."""
    path = arg.strip()
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return "\n".join(line.rstrip("\n") for line in fh)


def main(program_file: str | None = None):
    src = PROGRAM
    if program_file:
        with open(program_file, "r", encoding="utf-8") as fh:
            src = fh.read()
    vm = BasicVM(src)
    # pre-load live routes from the real conductor dispatcher
    vm.routes = [p for p, _ in _DISPATCHER._handlers]
    vm._helpers = {
        "count_routes": lambda: len(vm.routes),
        "get_routes": lambda: "",
        "route_at$": lambda i: vm.routes[i - 1] if 0 < i <= len(vm.routes) else "",
        # ledger / filesystem helpers (write to sovereign root, never OneDrive)
        "now$": lambda _: str(int(__import__("time").time())),
        "count_items$": lambda p: _count_items(p),
        "append_line$": lambda a: _ledger_append(a),
        "read_lines$": lambda f: _ledger_read(f),
        "cat$": lambda a: "".join(str(vm.eval_expr(x.strip())) for x in a.split(";")),
        "sp$": lambda a: _spark_for(a),
        "spark$": lambda c: _spark_for(c),
    }
    mode = "ledger" if program_file else "+ae://"
    print(f"qc64 BASIC chassis for {mode}  (dakk/qc64 MIT-style grammar)")
    vm.run()


if __name__ == "__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and arg.endswith(".bæsic"):
        main(program_file=arg)
    elif arg == "ledger":
        main(program_file=os.path.join(os.path.dirname(__file__), "ledger.bæsic"))
    else:
        main()
