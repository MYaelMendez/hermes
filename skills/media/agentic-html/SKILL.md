---
name: agentic-html
description: Build deterministic HTML media viewports (agentic.html) from Hermes media manifests for glocal distribution.
version: 1.0.0
author: local
license: MIT
metadata:
  hermes:
    tags: [Media, HTML, Viewport, Glocal, Manifest]
prerequisites:
  commands: [python]
---

# agentic-html

Generate a portable `agentic.html` viewport from a Hermes media manifest.

## Purpose

This skill keeps execution local (Ollama + FFmpeg + VLC) while distributing a single HTML control/audit surface across contexts:

- VS Code WebView
- browser preview
- static artifact hosting
- store/index pages

## Inputs

- A media manifest JSON from `hermes media plan`, `hermes media coevolve`, or breakout-linked workflows.

## Output

- `agentic.html` deterministic viewport containing:
  - execution plan metadata
  - command display
  - integrity hashes
  - optional local input/output previews (audio/video)

## Quick Start

```bash
python skills/media/agentic-html/scripts/export_agentic_viewport.py \
  --manifest "%LOCALAPPDATA%/hermes/media/manifests/smoke-media.json" \
  --output "%LOCALAPPDATA%/hermes/media/viewports/agentic.html"
```

## Recommended Flow

1. Generate or update manifest via Hermes media commands.
2. Export HTML viewport with this skill.
3. Open the HTML in VS Code or browser.
4. Use the same manifest for deterministic reruns/audit.

## Notes

- This skill does not execute FFmpeg itself.
- It is a viewport/export layer on top of deterministic manifest execution.
- Keep local-only guarantees at runtime (no cloud fallback) when using glocal mode.
