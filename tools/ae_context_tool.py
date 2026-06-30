"""+æ — Agentic Entrepreneurship Context Tool.

When called, loads the agentic entrepreneurship context bundle into the
conversation. This includes: formation paths, NAICS classification, Stripe
payment readiness, agentic.html viewport generation, Reachy clerk embodiment,
domain Code Mode registry, and the #250 mission.

This is the first blueprint-level tool — above skills, below core.
"""
import json
import os
from typing import Any, Dict

from tools.registry import registry

# ── Context bundle ──────────────────────────────────────────────

AE_CONTEXT = {
    "language": {
        "+æ": "add agentic entrepreneurship context",
        "^æ": "compress to agentic notation",
        "$^æ": "execute agentic entrepreneurship",
        "#": "blueprint / ask / organizational intent",
        "$": "economic execution (requires confirmation)",
        ">_æ|": "live sovereign prompt",
    },
    "stack": {
        "Hermesᴴ": "conductor — routes intent, skills, blueprints",
        "NVIDIAᴺ": "compute — 121+ models via API",
        "Stripe$": "economics — global cash register",
        "Doolaᴰ": "formation — LLC / DAOLLC, 50% commission",
        "NAICS": "classification — live search API",
        "Reachyᴿ": "embodiment — clerk, protagonist",
        "Exoᴱˣᵒ": "glocal compute mesh",
        "æ.store": "namespace IQ — 13 domains as syntax",
    },
    "blueprints": {
        "#startabusiness": {
            "type": "blueprint (organizational, above skill)",
            "context": "+æ",
            "execution": "$startabusiness",
            "stack": "^hns",
            "formation": "^atlas / ^doola",
            "classify": "NAICS (live API)",
            "viewport": "agentic.html (9:16 mobile-first)",
            "embodiment": "Reachyᴿ clerk",
            "care": "#opensourceware #250",
        },
        "#daollc": "DAO LLC formation blueprint",
        "#reachy-clerk": "Reachy as Stripe clerk / DAOLLC operator",
        "#llmstore": "model combinator / intelligence storefront",
        "#clillc": "command line for company formation",
    },
    "naics_codes": {
        "541511": "Custom Computer Programming Services",
        "541512": "Computer Systems Design Services",
        "541519": "Other Computer Related Services",
        "513210": "Software Publishers",
        "518210": "Data Processing, Hosting, and Related Services",
        "541618": "Other Management Consulting Services",
        "611430": "Professional and Management Development Training",
        "541715": "R&D in Nanotech/Biotech/Physical/Engineering/Life Sciences",
    },
    "revenue_proof": {
        "customer": "Nicolas Enriquez",
        "purchase": "$267.30 (Doola LLC formation)",
        "commission": "$133.65 (50%)",
        "date": "Dec 11, 2025",
        "status": "PAID",
    },
    "mission": {
        "name": "#opensourceware #250",
        "goal": "Help start 250 American businesses",
        "challenge": "Challenge sponsors to help start 250,000",
        "philosophy": "OCW → OSW (democratize agency, not just knowledge)",
        "care": "We embody #opensourceware and equip new business owners with care",
    },
    "security": {
        "# (blueprint)": "safe — no economic action, no formation",
        "$ (execution)": "requires user confirmation — cannot process payments or submit formation without explicit yes",
        "secrets": "never handles API keys, passwords, or credentials — routes humans to provider-owned flows",
    },
    "install": "hermes skills install https://myaelmendez.github.io/SKILL.md",
    "public_artifacts": [
        "https://myaelmendez.github.io/ae/",
        "https://myaelmendez.github.io/SKILL.md",
        "https://myaelmendez.github.io/PRIMITIVE.md",
        "https://myaelmendez.github.io/naics-blueprint.md",
        "https://myaelmendez.github.io/domain-stack.json",
    ],
}

# ── Activation / deactivation ──────────────────────────────────

_AE_ACTIVE = False


def is_ae_active() -> bool:
    """Check if +æ context is active in this session."""
    return _AE_ACTIVE


def activate_ae() -> dict:
    """Load agentic entrepreneurship context."""
    global _AE_ACTIVE
    _AE_ACTIVE = True
    return {
        "status": "active",
        "prompt": ">_æ|",
        "context": "+æ loaded",
        "language": AE_CONTEXT["language"],
        "stack": list(AE_CONTEXT["stack"].keys()),
        "blueprints": list(AE_CONTEXT["blueprints"].keys()),
        "mission": AE_CONTEXT["mission"]["name"],
        "message": "+æ context loaded. Prompt is now >_æ|. Hermes is the conductor. # asks, $ executes, | is live.",
    }


def deactivate_ae() -> dict:
    """Unload agentic entrepreneurship context."""
    global _AE_ACTIVE
    _AE_ACTIVE = False
    return {
        "status": "inactive",
        "prompt": ">_",
        "message": "-æ context unloaded. Prompt is now >_.",
    }


# ── Tool handler ────────────────────────────────────────────────

def ae_context_tool(action: str = "activate", query: str = "") -> str:
    """Handle +æ context operations.

    Args:
        action: "activate" (load +æ), "deactivate" (unload -æ),
                "search" (search blueprints/NAICS), "status" (check if active)
        query: search query when action is "search"

    Returns:
        JSON string with context data or search results.
    """
    action = (action or "activate").lower().strip()

    if action in ("activate", "+ae", "+æ", "load"):
        return json.dumps(activate_ae(), indent=2)

    elif action in ("deactivate", "-ae", "-æ", "unload"):
        return json.dumps(deactivate_ae(), indent=2)

    elif action == "status":
        return json.dumps({
            "active": _AE_ACTIVE,
            "prompt": ">_æ|" if _AE_ACTIVE else ">_",
        }, indent=2)

    elif action in ("search", "naics", "classify"):
        # Try live NAICS API if key is set
        naics_key = os.environ.get("NAICS_API_KEY", "")
        if naics_key and query:
            try:
                import urllib.request
                import urllib.parse
                url = f"https://api.naics.com/api/search?q={urllib.parse.quote(query)}&limit=5"
                req = urllib.request.Request(url, headers={
                    "X-API-Key": naics_key,
                    "Accept": "application/json",
                })
                with urllib.request.urlopen(req, timeout=15) as r:
                    api_data = json.loads(r.read())
                results = [
                    {
                        "code": item.get("code"),
                        "title": item.get("title"),
                        "description": (item.get("description") or "")[:120],
                    }
                    for item in api_data.get("data", [])[:5]
                ]
                return json.dumps({
                    "source": "live NAICS API",
                    "query": query,
                    "results": results,
                }, indent=2)
            except Exception as e:
                pass

        # Static fallback
        return json.dumps({
            "source": "static",
            "query": query,
            "codes": AE_CONTEXT["naics_codes"],
        }, indent=2)

    elif action in ("blueprints", "blueprint"):
        return json.dumps({
            "blueprints": AE_CONTEXT["blueprints"],
        }, indent=2)

    elif action in ("revenue", "proof"):
        return json.dumps(AE_CONTEXT["revenue_proof"], indent=2)

    elif action in ("mission", "challenge"):
        return json.dumps(AE_CONTEXT["mission"], indent=2)

    elif action in ("install", "skill"):
        return json.dumps({
            "install": AE_CONTEXT["install"],
            "artifacts": AE_CONTEXT["public_artifacts"],
        }, indent=2)

    else:
        return json.dumps({
            "error": f"unknown action: {action}",
            "actions": ["activate", "deactivate", "status", "search", "blueprints", "revenue", "mission", "install"],
        }, indent=2)


# ── Schema ──────────────────────────────────────────────────────

AE_SCHEMA = {
    "name": "ae_context",
    "description": (
        "+æ — Agentic Entrepreneurship context primitive. "
        "Load agentic entrepreneurship context (+æ), search NAICS business classifications (live API), "
        "discover blueprints, view revenue proof, and check mission status. "
        "When activated, the prompt becomes >_æ| and # (blueprint) / $ (execution) boundaries are enforced. "
        "Actions: activate, deactivate, status, search, blueprints, revenue, mission, install."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform: activate (+æ), deactivate (-æ), status, search (NAICS), blueprints, revenue, mission, install",
                "default": "activate",
                "enum": ["activate", "deactivate", "status", "search", "blueprints", "revenue", "mission", "install"],
            },
            "query": {
                "type": "string",
                "description": "Search query for NAICS classification (used with action=search)",
                "default": "",
            },
        },
        "required": [],
    },
}


def check_ae_requirements() -> bool:
    """+æ is always available — no external deps needed for activation."""
    return True


# ── Registry ────────────────────────────────────────────────────

registry.register(
    name="ae_context",
    toolset="ae",
    schema=AE_SCHEMA,
    handler=lambda args, **kw: ae_context_tool(
        action=args.get("action", "activate"),
        query=args.get("query", ""),
    ),
    check_fn=check_ae_requirements,
    emoji="æ",
)
