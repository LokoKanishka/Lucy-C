# Implement Clawdbot CLI Integration in Lucy-C

The goal is to resolve the 405 error in `clawdbot_llm.py` by switching from the HTTP `/v1/chat/completions` endpoint to the `clawdbot agent` CLI.

## User Review Required

> [!IMPORTANT]
> This change switches from a direct HTTP API call to a subprocess call to the `clawdbot` CLI. Ensure that the `clawdbot` CLI is available in the environment's PATH.

## Proposed Changes

### Dynamic Model Switching
Enable the model selector for Clawdbot and ensure the backend uses the selected model.

#### [MODIFY] [chat.js](file:///home/lucy-ubuntu/Lucy-C/lucy_c/web/static/js/chat.js)
- Allow `modelSelector` to be enabled when provider is `clawdbot`.

#### [MODIFY] [clawdbot_llm.py](file:///home/lucy-ubuntu/Lucy-C/lucy_c/lucy_c/clawdbot_llm.py)
- Update `generate` to accept `model` parameter and pass it to the CLI.

#### [MODIFY] [ollama_llm.py](file:///home/lucy-ubuntu/Lucy-C/lucy_c/lucy_c/ollama_llm.py)
- Update `generate` to accept `model` parameter.

#### [MODIFY] [pipeline.py](file:///home/lucy-ubuntu/Lucy-C/lucy_c/lucy_c/pipeline.py)
- Update `_generate_reply` to pass the model from config to the LLM.

### [lucy_c]

#### [MODIFY] [clawdbot_llm.py](file:///home/lucy-ubuntu/Lucy-C/lucy_c/clawdbot_llm.py)
- Replace `httpx.Client` logic with `subprocess.run`.
- Call `clawdbot agent --agent main --message "<prompt>" --json`.
- Parse the JSON output to extract the assistant's reply.

## Verification Plan

### Automated Tests
- Run `clawdbot agent --agent main --message "Hola" --json` manually to verify CLI output format.
- Run Lucy-C and switch to Clawdbot provider via the UI (or config).

### Manual Verification
- Verify that sending a message in the Lucy-C Web UI with Clawdbot provider correctly invokes the CLI and displays the response.
