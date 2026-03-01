# Integration: LM Studio <-> n8n

## Overview
This document outlines the steps to connect your local LM Studio instance (hosting the `gpt-oss-120b` model) with the n8n container, enabling the "Zero-Learning" automation architecture.

## 1. LM Studio Setup (The Brain)
**Prerequisites:**
- LM Studio installed on the host machine.
- `gpt-oss-120b` model downloaded and loaded.
- GPU Offloading enabled (as much as VRAM permits).

**Configuration:**
1.  Open LM Studio.
2.  Navigate to the **Local Server** tab (`<->` icon).
3.  Select the model `gpt-oss-120b` from the dropdown.
4.  **Server Port:** `1234` (Default).
5.  **Cross-Origin-Resource-Sharing (CORS):** Enable "ON" (Usually required for API access).
6.  Click **Start Server**.

**Verification:**
Test the server with a `curl` command from your host terminal:
```bash
curl http://localhost:1234/v1/models
```
You should receive a JSON response listing the loaded model.

## 2. n8n Connection (The Bridge)
**Prerequisite:** Ensure the n8n container is running (`docker-compose up -d`).

1.  Open n8n in your browser: `http://localhost:5678`.
2.  Go to **Credentials** -> **Add Credential**.
3.  Search for **OpenAI**.
4.  **Name:** `LM Studio - 120B` (or similar).
5.  **Type:** Select `OpenAI API`.
6.  **Configuration:**
    *   **API Key:** `lm-studio` (This is a placeholder, LM Studio usually accepts any string, but check if you set one).
    *   **Base URL:** `http://host.docker.internal:1234/v1`
        *   *Note:* `host.docker.internal` allows the Docker container to access the host machine's localhost.

## 3. Usage in Workflows
When using the "OpenAI Chat Model" node in n8n:
- **Credential:** Select the `LM Studio - 120B` credential you created.
- **Model:** Manually type `gpt-oss-120b` (or the exact ID returned in step 1 verification).
- **Prompt:** Connect your inputs as usual.

## Troubleshooting
- **Connection Refused:** Ensure LM Studio server is actually running.
- **Timeout:** Large models can verify slow. Increase the timeout settings in n8n if possible, or ensure the model is offloaded enough to be responsive.
- **Network Issues:** If `host.docker.internal` doesn't work (Linux sometimes requires extra config), try using the host's actual LAN IP (e.g., `192.168.1.X`).
