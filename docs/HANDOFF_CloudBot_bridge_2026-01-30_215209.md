# Handoff — CloudBot/Clawdbot bridge (Lucy-C) — 2026-01-30

## Contexto
Objetivo: usar Lucy-C como interfaz de voz (push-to-talk) y conectar “manos/ojos” de Clawdbot/CloudBot.

## Estado del sistema (Clawdbot)
- Gateway: systemd user service running en ws://127.0.0.1:18789
- Node host: `clawdbot-node.service` instalado y corriendo (paired/connected)
- Node caps: browser, system
- Node commands expuestos: browser.proxy, system.run, system.which, system.execApprovals.get/set

## Exec approvals
- `system.run` estaba bloqueado por approvals.
- Se habilitó allowlist mínima para `/usr/bin/ls` y `/usr/bin/pwd` en el node.
- Con eso `system.run` ejecuta y devuelve stdout correctamente (ej: listar ~/Escritorio).

## Lucy-C
- Lucy-C venv ve `clawdbot` en PATH.
- Bug identificado: `lucy_c/clawdbot_llm.py` usa endpoint hardcodeado `/v1/chat/completions` que devuelve 405.
- Switch principal: `lucy_c/pipeline.py` instancia/usa `ClawdbotLLM`.

## Próximo paso
- Abrir `pipeline.py` y `clawdbot_llm.py` para reemplazar HTTP `/v1/chat/completions` por mecanismo correcto:
  - Opción A: Clawdbot como tools backend (CLI): nodes invoke system.run + browser.*
  - Opción B: Clawdbot agent turn via `clawdbot agent` (requiere modelo local configurado en Clawdbot).
