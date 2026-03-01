# Project LUCY: Sovereign AI Automation Protocol
> **NiN — Network in Network | Zero Cloud Leak | $0 SaaS**

## 📖 Abstract
Project LUCY is a sovereign automation system designed for academic research, philosophy, and high-complexity task orchestration. It leverages a massive **120B parameter Mixture-of-Experts (MoE)** model as the "Architect" for reasoning and planning, while **n8n** serves as the "Executor" for cross-platform integration and file management.

The core philosophy is **Data Sovereignty**: 100% on-premise execution, $0 SaaS dependency, and total privacy.

---

## 🚀 Quick Start

### 1. The Brain: LM Studio Setup
1. **Download the Model:** Run the setup script to download `gpt-oss-120b` (GGUF format):
   ```bash
   python3 scripts/download_model.py
   ```
2. **Load:** Open LM Studio and load the model with maximum GPU offloading.
3. **Local Server:** Start the local server on `http://localhost:1234`.

### 2. The Body: n8n Docker Startup
From the **project root** (`~/Escritorio/NIN`):
```bash
docker-compose up -d
```
Access the interface at `http://localhost:5678/home/workflows`.

> **Tip:** Use the **NIN** desktop shortcut to open the workflows panel directly with one click.

### 3. The Bridge: Integration
In n8n, create an **OpenAI API** credential:
- **Base URL:** `http://host.docker.internal:1234/v1`
- **Model:** `gpt-oss-120b`

---

## 🔧 Troubleshooting

### UI doesn't load after system reboot or Docker restart
After a `sudo systemctl restart docker`, existing containers may lose their port mappings. Fix with:
```bash
cd ~/Escritorio/NIN
docker-compose down && docker-compose up -d --force-recreate
```
Verify connectivity:
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5678
# Expected: 200
```

### DNS errors in n8n logs (`EAI_AGAIN`)
Errors contacting `telemetry.n8n.io` or `posthog.com` are **expected and harmless** — the system operates in Zero Cloud Leak mode and these telemetry hosts are intentionally unreachable.

---

## 🏗 Hardware Architecture
| Component | Spec |
|-----------|------|
| CPU | AMD Ryzen 9 7950X |
| GPU | NVIDIA RTX 5090 (32GB VRAM) — Primary Inference |
| RAM | 128GB DDR5 — Offloading support |
| Storage | Gen 5 NVMe — Ultra-fast model loading |

---

## 🧠 Software Components

### 1. The Architect (`gpt-oss-120b`)
Generates logical plans and **valid n8n workflow JSON** from natural language instructions. See `prompts/architect_prompt.md`.

### 2. The Executor (n8n)
Orchestrates file reading (PDFs, CSVs), API calls, and Markdown report generation. Operates autonomously from the Architect's JSON output.

---

## 📂 Project Structure
```
NIN/
├── docker-compose.yml       # Sovereign n8n environment
├── data/                    # Shared input/output folder (mounted to /data in n8n)
├── docs/
│   ├── integration_config.md
│   └── sample_workflow.json
├── prompts/
│   └── architect_prompt.md  # Logical core of the system
├── models/                  # GGUF model storage
├── find_models.py
└── nin_client.py            # Remote workflow activation via webhooks
```

## 🛡 Security & Ethics
- **Zero Cloud Leak:** All reasoning and data processing stay within your local network.
- **Zero SaaS Cost:** No OpenAI, no Zapier, no cloud dependencies.
- **Academic Rigor:** Designed for deep textual analysis and philosophical research.

---
*Mantenido por Project LUCY — 2026*
