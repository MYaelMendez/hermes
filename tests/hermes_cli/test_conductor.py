"""Policy tests for the standalone scheme dispatcher in conductor."""
from __future__ import annotations

import pytest

from hermes_cli.conductor import (
    SchemeDispatcher,
    _dispatch,
    _is_scheme_cmd,
    run_hermes,
)


@pytest.fixture()
def dispatcher() -> SchemeDispatcher:
    each = SchemeDispatcher()
    each.register("c://cc", lambda raw: {"ok": True, "stdout": f"cctx:{raw}\n"})
    each.register(
        "pc://run",
        lambda raw, name: {"ok": True, "stdout": f"pc_run:{raw}\n"},
    )
    each.register("pc://", lambda raw: {"ok": True, "stdout": f"pc:{raw}\n"})
    each.register("mcp://", lambda raw: {"ok": True, "stdout": f"mcp:{raw}\n"})
    each.register("custom://", lambda raw: {"ok": True, "stdout": f"custom:{raw}\n"})
    return each


def test_register_dispatches_first_match(dispatcher: SchemeDispatcher) -> None:
    assert dispatcher.dispatch("c://cc +æ://ops")["stdout"] == "cctx:c://cc +æ://ops\n"
    assert dispatcher.dispatch("pc://run alpha")["stdout"] == "pc_run:pc://run\n"
    assert dispatcher.dispatch("pc://")["stdout"] == "pc:pc://\n"
    assert dispatcher.dispatch("mcp://tools")["stdout"] == "mcp:mcp://tools\n"


def test_register_overlaps_preserve_longest_prefix() -> None:
    each = SchemeDispatcher()
    each.register(
        "c://",
        lambda raw: {"ok": False, "stdout": "unexpected"},
    )
    each.register("c://cc", lambda raw: {"ok": True, "stdout": "expected"})
    result = each.dispatch("c://cc +æ://ops")
    assert result == {"ok": True, "stdout": "expected"}


def test_is_scheme_cmd_when_matched(dispatcher: SchemeDispatcher) -> None:
    assert dispatcher.is_scheme_cmd("mcp://tools") is True
    assert dispatcher.is_scheme_cmd("pc://run default") is True
    assert dispatcher.is_scheme_cmd("c://cc daollc://") is True


def test_is_scheme_cmd_unknown() -> None:
    assert _is_scheme_cmd("random command") is False
    assert _is_scheme_cmd("") is False


def test_dispatch_unknown_scheme() -> None:
    result = _dispatch("foo://bar")
    assert result["ok"] is False
    assert result["rc"] == 2
    assert "unsupported scheme" in result["stderr"]


def test_default_dispatcher_handles_builtin_schemes() -> None:
    builtin = {
        "c://cc +æ://ops",
        "pc://run alpha",
        "pc://",
        "mcp://tools",
        "vscode://",
        "reachy://",
        "NOUS://",
        "llc://",
        "daollc://",
        "commandprompt://",
        "home://",
        "fs://",
        "fs://stat C:/æ/hermes-fork",
        "fs://tree C:/æ/hermes-fork",
    }
    for command in builtin:
        result = _dispatch(command)
        assert result["ok"] is True, command
        assert result["stdout"]
        assert "surface" in result
    identity_result = _dispatch("+æ://identity")
    assert identity_result["ok"] is True
    assert identity_result["surface"]["kind"] == "bounded_private_client_mesh"
    assert identity_result["surface"]["conductor"] == "hermes-agent/conductor"
    action_result = _dispatch("+æ://conductor plan")
    assert action_result["ok"] is True
    assert action_result["surface"]["kind"] == "ae_engineering_hub"
    assert action_result["surface"]["action"] == "plan"


def test_run_hermes_scheme_scheme_property() -> None:
    result = run_hermes({"cmd": "mcp://tools"})
    assert result["scheme"] == "mcp"
    assert result["ok"] is True


def test_run_hermes_cli_verb_passthrough() -> None:
    result = run_hermes({"cmd": "viewport status"})
    # unknown verbs should not claim scheme dispatch; they fall through to CLI
    assert "unsupported scheme" not in result.get("stderr", "")


def test_run_hermes_missing_cmd() -> None:
    result = run_hermes({})
    assert result["ok"] is False
    assert result["rc"] == 2
    assert result["stdout"] == ""
    assert result["stderr"] == "missing cmd"
    assert result["surface"] == {"kind": "invalid"}


def test_run_hermes_preserves_run_pc_default() -> None:
    result = run_hermes({"cmd": "run pc://"})
    assert result["ok"] is True
    assert "pc://run default" in result["stdout"]
    assert result["surface"]["client"] == "default"


def test_policy_surface_keys_present_for_builtins() -> None:
    cases = {
        "pc://": ("private_client",),
        "pc://run beta": ("private_client_run", "beta"),
        "c://cc +æ://ops": ("cctx",),
        "NOUS://": ("provider",),
        "vscode://": ("viewport_host",),
        "reachy://": ("robot",),
        "mcp://tools": ("mcp",),
        "daollc://": ("dao",),
        "+æ://ops": ("aectx",),
        "commandprompt://": ("commandprompt",),
        "home://": ("os_home",),
        "fs://": ("fs",),
        "fs://stat C:/æ/hermes-fork": ("fs",),
        "fs://read C:/æ/hermes-fork/AGENTS.md": ("fs",),
        "fs://tree C:/æ/hermes-fork": ("fs",),
    }
    for command, expected_kinds in cases.items():
        result = _dispatch(command)
        assert result["ok"] is True, command
        assert result["surface"]["kind"] in expected_kinds
        if len(expected_kinds) == 2:
            assert result["surface"].get("client") == expected_kinds[1]
    home = _dispatch("home://")
    assert set(home["surface"]["entrypoints"]) == {
        "terminal", "editor", "files", "victus", "nvidia", "vlc", "ffmpeg", "qr", "mesh"
    }
    assert home["surface"]["entrypoints"]["files"] == "fs://"


def test_cc_dispatch_routes_to_gpu_mcp() -> None:
    """+æ://cc is the command & control surface -> local GPU-MCP (CUDA + Rust/WASM)."""
    result = _dispatch("+æ://cc home://")
    assert result["ok"] is True
    assert result["scheme_detail"] == "+æ://cc"
    assert result["surface"]["kind"] == "mcp"
    assert result["surface"]["address"] == "mcp://gpu-mcp"
    assert result["surface"]["launch"] == "python -m gpu_mcp"


def test_cc_longer_prefix_outranks_bare_aectx() -> None:
    """+æ://cc must win over the +æ:// (aectx) catch-all for cc subcommands."""
    cc = _dispatch("+æ://cc home://")
    bare = _dispatch("+æ://ops")
    assert cc["scheme_detail"] == "+æ://cc"
    assert bare["surface"]["kind"] == "aectx"


def test_glocal_agent_dispatch_routes_to_gpu_mcp() -> None:
    """æ://glocal-agent is the canonical name for the sovereign local agent
    primitive (+æ^glocal) -> local GPU-MCP (alias of +æ://cc home://)."""
    result = _dispatch("æ://glocal-agent home://")
    assert result["ok"] is True
    assert result["scheme_detail"] == "æ://glocal-agent"
    assert result["surface"]["kind"] == "mcp"
    assert result["surface"]["address"] == "mcp://gpu-mcp"
    assert result["surface"]["launch"] == "python -m gpu_mcp"


def test_glocal_agent_short_form_defaults_to_home() -> None:
    result = _dispatch("æ://glocal-agent")
    assert result["ok"] is True
    assert result["scheme_detail"] == "æ://glocal-agent"
    assert result["surface"]["node"] == "home://"


def test_glocal_cloud_computer_is_hybrid_local_default() -> None:
    """+æ://glocal cloud computer resolves to a hybrid surface: local hands
    always, and a LOCAL brain by default (cloud is opt-in only)."""
    result = _dispatch("+æ://glocal cloud computer")
    assert result["ok"] is True
    assert result["scheme_detail"] == "+æ://glocal cloud computer"
    surf = result["surface"]
    assert surf["kind"] == "hybrid"
    # hands are ALWAYS the sovereign local gpu-mcp
    assert surf["hands"]["address"] == "mcp://gpu-mcp"
    assert surf["hands"]["launch"] == "python -m gpu_mcp"
    # brain defaults local — never silently cloud
    assert surf["brain"]["provider"] == "local"
    assert surf["brain"]["opt_in"] is False
    assert surf["brain"]["policy"] == "local-default; cloud-explicit-only"


def test_glocal_cloud_computer_opt_in_portal() -> None:
    """Explicit `portal` token flips the brain to Nous Portal (opt-in only)."""
    result = _dispatch("+æ://glocal cloud computer portal")
    assert result["surface"]["brain"]["provider"] == "nous-portal"
    assert result["surface"]["brain"]["opt_in"] is True


def test_mesh_qr_pairing_offer_accept() -> None:
    """+æ://mesh offer emits a QR; the scanned manifest accepts into a live
    pc://mesh/<name>/local route. Opt-in only; bad payload is rejected."""
    offer = _dispatch("+æ://mesh offer legion")
    assert offer["ok"] is True
    assert offer["surface"]["kind"] == "mesh_offer"
    assert offer["surface"]["route"] == "pc://mesh/legion/local"
    manifest = offer["surface"]["manifest"]
    assert manifest.startswith("ae://peer?host=legion")
    accept = _dispatch(f"+æ://mesh accept {manifest}")
    assert accept["ok"] is True
    peer = _dispatch("pc://mesh/legion/local")
    assert peer["ok"] is True
    assert peer["surface"]["address"] == "pc://mesh/legion/local"
    bad = _dispatch("+æ://mesh accept garbage")
    assert bad["ok"] is False





def test_viewport_scheme_is_the_mandate() -> None:
    """viewport:// is the mandate: the local HTML/CSS/WASM surface is the control
    plane. vscode:// is its host. The v in vscode = viewport, not Visual Studio."""
    vp = _dispatch("viewport://home://")
    assert vp["ok"] is True
    assert vp["surface"]["kind"] == "viewport"
    assert vp["surface"]["v"] == "viewport"
    vs = _dispatch("vscode://")
    assert vs["ok"] is True
    assert vs["surface"]["kind"] == "viewport_host"
    assert vs["surface"]["v"] == "viewport"


def test_viewport_hermes_agent_resolves_to_concrete_surface() -> None:
    """viewport://hermes-agent is the concrete instance: the Hermes Agent
    viewport (ae://glocal-agent primitive rendered local)."""
    r = _dispatch("viewport://hermes-agent")
    assert r["ok"] is True
    assert r["surface"]["node"] == "hermes-agent"
    assert r["surface"]["agent"] == "ae://glocal-agent"
    assert r["surface"]["control_surface"] == "mcp://gpu-mcp"
    assert r["surface"]["brain"] == "ollama://localhost:11434"
    assert r["surface"]["html"] == "templates/surfaces/index.html"


def test_ae_agentic_context_router() -> None:
    """æ:// is the agentic context router; bare +æ:// catch-all resolves to
    aectx (not dao). Longer prefixes still win over the catch-all."""
    bare = _dispatch("æ://pc://")
    assert bare["ok"] is True
    assert bare["surface"]["kind"] == "aectx"
    assert bare["surface"]["target"] == "pc://"
    assert bare["surface"]["active"] is True

    plus = _dispatch("+æ://ops")
    assert plus["surface"]["kind"] == "aectx"
    assert plus["surface"]["target"] == "ops"

    ga = _dispatch("æ://glocal-agent home://")
    assert ga["scheme_detail"] == "æ://glocal-agent"
    assert ga["surface"]["kind"] == "mcp"

    cc = _dispatch("+æ://cc home://")
    assert cc["scheme_detail"] == "+æ://cc"


def test_hermes_superagent_blocked_scalar_supremacy() -> None:
    """hermes-superagent:// is blocked at the chassis (scalar supremacy).

    No tier above the sovereign scalar; the language enforces the boundary so
    surfaces linking to it dead-end at the router. status must NOT resolve.
    """
    r = _dispatch("hermes-superagent://status")
    assert r["ok"] is False
    assert r["rc"] == 2
    assert r["surface"]["kind"] == "blocked"
    assert r["surface"]["reason"] == "scalar-supremacy"
    assert r["surface"]["route_through"] == "æ://"


def test_pc_reports_sovereign_mesh() -> None:
    """pc:// reports the canonical mesh; pc://<node> addresses a node on it."""
    bare = _dispatch("pc://")
    assert bare["surface"]["kind"] == "private_client"
    assert bare["surface"]["mesh"] == "pc://mesh/victus/local"
    assert bare["surface"]["node"] == "pc://mesh/victus/local"
    assert bare["surface"]["local_only"] is True

    node = _dispatch("pc://mesh/victus/local/vlc")
    assert node["surface"]["node"] == "mesh/victus/local/vlc"


def test_robot_scheme_with_reachy_flagship() -> None:
    """robot:// is the abstract embodiment scheme; reachy:// is the flagship.

    robot://reachy and reachy:// resolve to the same flagship surface; a
    generic robot://<model> resolves non-flagship. All ride the pc:// mesh.
    """
    reachy = _dispatch("reachy://")
    assert reachy["surface"]["kind"] == "robot"
    assert reachy["surface"]["model"] == "reachy"
    assert reachy["surface"]["flagship"] is True
    assert reachy["scheme_detail"] == "reachy://"
    assert reachy["surface"]["mesh"] == "pc://mesh/victus/local"

    via_robot = _dispatch("robot://reachy")
    assert via_robot["surface"]["model"] == "reachy"
    assert via_robot["surface"]["flagship"] is True

    generic = _dispatch("robot://arm42 pc://mesh/victus/local")
    assert generic["surface"]["kind"] == "robot"
    assert generic["surface"]["model"] == "arm42"
    assert generic["surface"]["flagship"] is False
    assert generic["surface"]["node"] == "pc://mesh/victus/local"


def test_desktop_surface_under_cc() -> None:
    """desktop:// is the generative desktop viewport, routed under +æ://cc.

    Native when the WindowsDesktop actuator is available; otherwise it
    degrades to intent-reporting. Either way it stays sovereign-scoped.
    """
    d = _dispatch("desktop://focus")
    assert d["surface"]["kind"] == "desktop"
    assert d["surface"]["action"] == "focus"
    assert d["surface"]["control"] == "+æ://cc"
    assert d["surface"]["node"] == "pc://mesh/victus/local"
    # native bridge present on Windows; intent-only fallback elsewhere
    assert d["surface"].get("native") in (True, False)

    bare = _dispatch("desktop://")
    assert bare["surface"]["action"] == "enumerate"


def test_cuda_vlc_surface_routing() -> None:
    """+æ://cuda-vlc routes to the CUDA→NVENC→VLC streaming surface.

    Hermetic: only exercises status/stop (no ffmpeg/VLC spawn) so the suite
    stays fast and headless. Live encode path is covered by ad-hoc verification.
    """
    assert _is_scheme_cmd("+æ://cuda-vlc play test") is True

    idle = _dispatch("+æ://cuda-vlc status")
    assert idle["surface"]["kind"] == "cuda_vlc_surface"
    assert idle["surface"]["runtime"] == "hermes-code"
    assert idle["live"] is False

    stopped = _dispatch("+æ://cuda-vlc stop")
    assert stopped["ok"] is True
    assert stopped["surface"]["command"] == "stop"

    unknown = _dispatch("+æ://cuda-vlc frobnicate")
    assert unknown["ok"] is False
    assert "unknown action" in unknown["stderr"]


# ── the schemes added this session: a:// · vidæo:// · video:// ──
# All hermetic: no GPU, no render, no network. The live render path is covered
# by ad-hoc verification (video://dji 5 → PASS), not the suite.


def test_a_ascii_alias_of_ae() -> None:
    """a:// is the typable ASCII alias for æ:// — same routes, no glyph needed.

    The glyph æ is not on every keyboard; `?` was the de-facto stand-in but is
    the URL query separator. `a` is the letter.
    """
    # recognized as a scheme BEFORE normalization
    assert _is_scheme_cmd("a://mesh") is True
    assert _is_scheme_cmd("+a://secrets") is True

    # a:// and æ:// dispatch identically
    a_mesh = _dispatch("a://mesh")
    ae_mesh = _dispatch("æ://mesh")
    assert a_mesh["ok"] is True
    assert ae_mesh["ok"] is True
    assert a_mesh["stdout"] == ae_mesh["stdout"]

    # the +a:// superset maps to +æ://
    a_secrets = _dispatch("+a://secrets")
    ae_secrets = _dispatch("+æ://secrets")
    assert a_secrets["ok"] == ae_secrets["ok"]
    assert (a_secrets.get("stderr") or a_secrets.get("stdout")) == \
           (ae_secrets.get("stderr") or ae_secrets.get("stdout"))


def test_vidaeo_brand_production_surface() -> None:
    """vidæo://<brand> resolves a brand to its surface + manifest."""
    assert _is_scheme_cmd("vidæo://aipodcast.me") is True

    index = _dispatch("vidæo://")
    assert index["ok"] is True
    assert index["scheme"] == "vidæo://"
    brands = {b["brand"] for b in index["surfaces"] if False} if False else \
             {b["brand"] for b in index.get("brands", [])}
    assert "aipodcast.me" in brands

    brand = _dispatch("vidæo://aipodcast.me")
    assert brand["ok"] is True
    assert brand["brand"] == "aipodcast.me"
    assert "aipodcast_me" in brand["surface"]

    # an unknown brand fails honestly, naming a known one
    bogus = _dispatch("vidæo://notabrand")
    assert bogus["ok"] is False
    assert "unknown action" in bogus["stderr"]


def test_video_render_request_surface() -> None:
    """video://<subject> is the render request surface over æRTXrender."""
    assert _is_scheme_cmd("video://dji") is True

    index = _dispatch("video://")
    assert index["ok"] is True
    assert index["scheme"] == "video://"
    assert index["default_seconds"] == 5
    subjects = {s["subject"] for s in index["surfaces"]}
    assert "dji" in subjects
    assert "zeitgeist" in subjects
    # the harness is named — this is æRTXrender, deterministically driven
    assert "æRTXrender" in index["harness"]

    # an unknown subject fails honestly, listing the known ones
    bogus = _dispatch("video://notasubject")
    assert bogus["ok"] is False
    assert "unknown subject" in bogus["stderr"]
    assert "dji" in bogus["stderr"]


def test_video_and_vidaeo_are_distinct_surfaces() -> None:
    """video:// is the ASK; vidæo:// is the BRAND/pipeline. Different verbs."""
    video = _dispatch("video://")
    vidaeo = _dispatch("vidæo://")
    assert video["scheme"] == "video://"
    assert vidaeo["scheme"] == "vidæo://"
    # video:// carries a harness + subjects; vidæo:// carries brands
    assert "harness" in video
    assert "brands" in vidaeo


def test_threejs_stack_surface() -> None:
    """three.js:// inspects the vendored Three.js stack — the renderer, addressed.

    Hermetic: reads the vendor directory only (no browser, no render, no GPU).
    """
    assert _is_scheme_cmd("three.js://addons") is True

    index = _dispatch("three.js://")
    assert index["ok"] is True
    assert index["scheme"] == "three.js://"
    assert index["revision"].isdigit()
    counts = index["counts"]
    assert counts["surfaces"] >= 1
    assert counts["addons"] >= 1
    # the four inspection verbs are advertised
    assert set(index["actions"]) == {"version", "check", "addons", "surfaces", "curriculum"}

    version = _dispatch("three.js://version")
    assert version["ok"] is True
    assert "three.core.js" in version["files"]
    assert version["files"]["three.core.js"]["exists"] is True

    check = _dispatch("three.js://check")
    assert check["ok"] is True
    assert check["intact"] is True

    addons = _dispatch("three.js://addons")
    assert addons["ok"] is True
    assert "postprocessing" in addons["addons"]
    # EffectComposer is the post chain the render harness depends on
    assert "EffectComposer" in addons["addons"]["postprocessing"]

    surfaces = _dispatch("three.js://surfaces")
    assert surfaces["ok"] is True
    assert surfaces["count"] >= 1
    # renderable surfaces expose __renderFrame — the deterministic hook
    assert surfaces["renderable"] >= 1


def test_the_four_scheme_verbs_are_distinct() -> None:
    """video:// ASK · vidæo:// BRAND · three.js:// STACK · a:// ALIAS.

    Four surfaces answering four different questions. Collapsing them would lose
    the distinction the mesh is built on.
    """
    ask = _dispatch("video://")
    brand = _dispatch("vidæo://")
    stack = _dispatch("three.js://")
    assert ask["scheme"] == "video://"
    assert brand["scheme"] == "vidæo://"
    assert stack["scheme"] == "three.js://"
    # each carries its own vocabulary
    assert "harness" in ask and "default_seconds" in ask
    assert "brands" in brand
    assert "revision" in stack and "counts" in stack


def test_hyperframes_monorepo_surface() -> None:
    """hyperframes:// inspects the HyperFrames monorepo — the framework, addressed.

    Hermetic: reads the monorepo directory only (no bun, no build, no network).
    """
    assert _is_scheme_cmd("hyperframes://packages") is True

    index = _dispatch("hyperframes://")
    assert index["ok"] is True
    assert index["scheme"] == "hyperframes://"
    counts = index["counts"]
    assert counts["packages"] >= 1
    assert counts["blocks"] >= 1
    assert counts["skills"] >= 1
    assert set(index["actions"]) == {"packages", "registry", "skills", "check", "relation"}

    packages = _dispatch("hyperframes://packages")
    assert packages["ok"] is True
    names = {p["name"] for p in packages["packages"]}
    # the capture engine and the CLI are the load-bearing packages
    assert "engine" in names
    assert "cli" in names

    registry = _dispatch("hyperframes://registry")
    assert registry["ok"] is True
    assert registry["registry"]["blocks"]
    assert len(registry["registry"]["blocks"]) == registry["count"] - \
        len(registry["registry"]["components"]) - len(registry["registry"]["examples"])

    skills = _dispatch("hyperframes://skills")
    assert skills["ok"] is True
    assert any(s["name"] == "hyperframes" for s in skills["skills"])

    # relation names its sibling — the two stacks are not the same thing
    rel = _dispatch("hyperframes://relation")
    assert rel["ok"] is True
    assert "æRTXrender" in rel["stdout"]


def test_hyperframes_check_is_honest() -> None:
    """hyperframes://check reports ok=False when the monorepo is not runnable.

    A build check that always says 'fine' is worse than none. This one names what
    is missing (bun, node_modules, dist) and how to fix it.
    """
    check = _dispatch("hyperframes://check")
    # ok mirrors the real runnable state — do not assert a value, assert the shape
    assert "bun" in check
    assert "node_modules" in check
    assert "packages_with_dist" in check
    assert "runnable:" in check["stdout"]
    assert "bun install" in check["stdout"]
    # ok must agree with its own evidence
    evidence_ok = bool(check["bun"]) and check["node_modules"] and check["packages_with_dist"] > 0
    assert check["ok"] == evidence_ok


def test_two_stack_surfaces_are_distinct() -> None:
    """three.js:// is the RENDERER; hyperframes:// is the FRAMEWORK."""
    three = _dispatch("three.js://")
    hf = _dispatch("hyperframes://")
    assert three["scheme"] == "three.js://"
    assert hf["scheme"] == "hyperframes://"
    # the renderer carries a revision; the framework carries a package version
    assert "revision" in three
    assert "version" in hf
    # each has its own vocabulary — addons vs packages/registry/skills
    assert "counts" in three and "addons" in three["counts"]
    assert "counts" in hf and "packages" in hf["counts"]


def test_supervisionvidaeo_contract_surface() -> None:
    """supervisionvidaeo:// exposes the produce-and-verify contract.

    Hermetic for the metadata actions (index/api/bounds/toolchain/check) — they
    read the package, not a video. The live gate is covered by ad-hoc
    verification (verify dji-5s.mp4 → PASS), not the suite.
    """
    assert _is_scheme_cmd("supervisionvidaeo://toolchain") is True

    index = _dispatch("supervisionvidaeo://")
    assert index["ok"] is True
    assert index["scheme"] == "supervisionvidaeo://"
    # the contract is the point: produce() → Receipt, or refuse
    assert "SupervisionRefused" in index["stdout"]
    assert "Receipt" in index["stdout"]
    assert set(index["actions"]) == {"toolchain", "bounds", "api", "verify <mp4>", "check"}

    api = _dispatch("supervisionvidaeo://api")
    assert api["ok"] is True
    assert "produce" in api["api"]
    assert "verify" in api["api"]
    # the refusal is named, not hidden
    assert "SupervisionRefused" in api["api"]
    # SceneSpec.bounded clamps — it must not raise
    assert "bounded" in "".join(api["api"].keys()) or \
           any("bounded" in k for k in api["api"])

    bounds = _dispatch("supervisionvidaeo://bounds")
    assert bounds["ok"] is True
    assert "particles" in bounds["bounds"]
    assert "duration" in bounds["bounds"]
    assert isinstance(bounds["bounds"]["particles"], list)

    check = _dispatch("supervisionvidaeo://check")
    # check mirrors the real importable+usable state
    assert "usable:" in check["stdout"]


def test_supervisionvidaeo_verify_fails_honestly() -> None:
    """A verify with no path, or a missing file, returns ok=False — never a fake PASS.

    The whole contract is 'never return a path to a broken file'. A verify that
    says PASS on a file it never opened would break that.
    """
    no_path = _dispatch("supervisionvidaeo://verify")
    assert no_path["ok"] is False
    assert "no path" in no_path["stderr"]

    missing = _dispatch("supervisionvidaeo://verify C:/definitely/not/here.mp4")
    assert missing["ok"] is False
    assert "not found" in missing["stderr"]


def test_six_scheme_verbs_are_distinct() -> None:
    """Six surfaces, six questions — ASK · BRAND · RENDERER · FRAMEWORK · CONTRACT · ALIAS."""
    schemes = {
        "video://": "video://",
        "vidæo://": "vidæo://",
        "three.js://": "three.js://",
        "hyperframes://": "hyperframes://",
        "supervisionvidaeo://": "supervisionvidaeo://",
    }
    for probe, expected in schemes.items():
        r = _dispatch(probe)
        assert r["scheme"] == expected, probe
    # each carries a distinct vocabulary
    assert "harness" in _dispatch("video://")
    assert "brands" in _dispatch("vidæo://")
    assert "revision" in _dispatch("three.js://")
    assert "version" in _dispatch("hyperframes://")
    assert "bounds" in _dispatch("supervisionvidaeo://")


def test_vscode_bridge_surface() -> None:
    """vscode:// exposes the VSCODER://BRIDGE — VS Code as the agentic terminal.

    Hermetic: reads the bridge source files only (no VS Code, no WebSocket).
    """
    assert _is_scheme_cmd("vscode://bridge") is True

    index = _dispatch("vscode://")
    assert index["ok"] is True
    assert index["scheme"] == "vscode://"
    assert "VSCODER://BRIDGE" in index["stdout"]
    assert set(index["actions"]) == {"bridge", "state", "resolver", "plan", "capabilities", "events"}

    bridge = _dispatch("vscode://bridge")
    assert bridge["ok"] is True
    assert "JSON-RPC" in bridge["stdout"]
    assert "localhost" in bridge["stdout"]
    assert "64 KB" in bridge["stdout"]

    state = _dispatch("vscode://state")
    assert state["ok"] is True
    assert "VSCODER_IDE_STATE_V1" in state["stdout"]
    assert "IDEStateObserver" in state["stdout"]

    resolver = _dispatch("vscode://resolver")
    assert resolver["ok"] is True
    assert "CommandResolver" in resolver["stdout"]
    assert "LOCAL" in resolver["stdout"] or "DURABLE" in resolver["stdout"] or "EXTERNAL" in resolver["stdout"]

    plan = _dispatch("vscode://plan")
    assert plan["ok"] is True
    assert "PlanValidator" in plan["stdout"]
    assert "409" in plan["stdout"]

    capabilities = _dispatch("vscode://capabilities")
    assert capabilities["ok"] is True
    assert capabilities["count"] >= 1
    assert len(capabilities["namespaces"]) >= 1

    events = _dispatch("vscode://events")
    assert events["ok"] is True
    assert "EventStream" in events["stdout"]
    assert "sanitize" in events["stdout"]


def test_vscode_is_distinct_from_other_schemes() -> None:
    """vscode:// is the IDE/terminal surface — not a render or brand surface."""
    vscode = _dispatch("vscode://")
    video = _dispatch("video://")
    vidaeo = _dispatch("vidæo://")
    assert vscode["scheme"] == "vscode://"
    assert video["scheme"] == "video://"
    assert vidaeo["scheme"] == "vidæo://"
    # vscode carries bridge modules; video carries a harness; vidaeo carries brands
    assert "modules" in vscode
    assert "harness" in video
    assert "brands" in vidaeo
