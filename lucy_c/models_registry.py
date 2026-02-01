from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ModelMetadata:
    name: str
    size_gb: float
    description: str
    strengths: List[str]
    is_recommended: bool = False

# Lucy's curated whitelist of models
LUCY_RECOMMENDED = {
    "llama3:8b": ModelMetadata(
        name="llama3:8b",
        size_gb=4.7,
        description="Meta Llama 3 (8B). Excelente balance general.",
        strengths=["diálogo", "razonamiento", "español"],
        is_recommended=True
    ),
    "mistral:7b": ModelMetadata(
        name="mistral:7b",
        size_gb=4.1,
        description="Mistral 7B. Rápido y conciso.",
        strengths=["resumen", "velocidad", "instrucciones"],
        is_recommended=True
    ),
    "codellama:7b": ModelMetadata(
        name="codellama:7b",
        size_gb=3.8,
        description="CodeLlama 7B. Especializado en programación.",
        strengths=["código", "python", "debug"],
        is_recommended=True
    ),
    "phi3:mini": ModelMetadata(
        name="phi3:mini",
        size_gb=2.3,
        description="Microsoft Phi-3 Mini. Muy liviano y capaz.",
        strengths=["razonamiento", "dispositivos_limitados"],
        is_recommended=True
    ),
    "dolphin-llama3:8b": ModelMetadata(
        name="dolphin-llama3:8b",
        size_gb=4.7,
        description="Llama 3 sin censura (Dolphin). Más creativo y directo.",
        strengths=["creatividad", "sin_censura"],
        is_recommended=True
    ),
    "qwen2:7b": ModelMetadata(
        name="qwen2:7b",
        size_gb=4.4,
        description="Qwen 2 (7B). Muy bueno en razonamiento matemático y técnico.",
        strengths=["técnico", "matemáticas"],
        is_recommended=True
    )
}

def enrich_model_info(model_name: str, ollama_data: Dict[str, Any]) -> ModelMetadata:
    """Combines Ollama API data with Lucy's curated metadata."""
    # Find base name (without tags if necessary, though Ollama usually matches)
    base_name = model_name.split(":")[0]
    
    # Try exact match first
    meta = LUCY_RECOMMENDED.get(model_name)
    if not meta:
        # Try base name match
        meta = LUCY_RECOMMENDED.get(base_name)
        
    size_bytes = ollama_data.get("size", 0)
    size_gb = round(size_bytes / (1024**3), 1)

    if meta:
        # Return matched meta but update size to actual installed size
        return ModelMetadata(
            name=model_name,
            size_gb=size_gb,
            description=meta.description,
            strengths=meta.strengths,
            is_recommended=True
        )
    
    # Generic metadata for unknown models
    return ModelMetadata(
        name=model_name,
        size_gb=size_gb,
        description="Modelo instalado localmente.",
        strengths=["general"],
        is_recommended=False
    )

def get_enriched_models_list(ollama_models: List[Dict[str, Any]]) -> List[ModelMetadata]:
    """Processes a list of models from Ollama API return objects."""
    enriched = []
    for m in ollama_models:
        name = m.get("name")
        if name:
            enriched.append(enrich_model_info(name, m))
    
    # Sort: recommended first, then by name
    return sorted(enriched, key=lambda x: (not x.is_recommended, x.name))
