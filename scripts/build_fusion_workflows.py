#!/usr/bin/env python3
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "integration" / "workflows_fusion"


def slugify(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return clean or "workflow"


def sanitize_workflow(source: str, src_path: Path, raw: dict, force_name: str | None = None) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("El JSON no es un objeto.")

    name = str(raw.get("name") or src_path.stem).strip()
    if not name:
        name = src_path.stem

    nodes = raw.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("Campo nodes invalido.")

    connections = raw.get("connections", {})
    if not isinstance(connections, dict):
        raise ValueError("Campo connections invalido.")

    settings = raw.get("settings", {})
    if not isinstance(settings, dict):
        settings = {}

    final_name = force_name if force_name else f"{source.upper()} | {name}"

    return {
        "name": final_name,
        "nodes": nodes,
        "connections": connections,
        "settings": settings,
    }


def iter_sources():
    nin_dir = ROOT / "upstream" / "NiN" / "workflows"
    for path in sorted(nin_dir.glob("*.json")):
        yield "nin", path

    cun_dir = ROOT / "upstream" / "cunningham-Espejo"
    for path in sorted(cun_dir.glob("workflow*.json")):
        yield "cunningham", path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.json"):
        old.unlink()

    manifest = []
    written = 0
    skipped = 0

    name_counts: dict[str, int] = {}
    for source, src_path in iter_sources():
        try:
            raw = json.loads(src_path.read_text(encoding="utf-8"))
            preview = sanitize_workflow(source, src_path, raw)
            base_name = preview["name"]
            suffix_count = name_counts.get(base_name, 0)
            name_counts[base_name] = suffix_count + 1
            if suffix_count > 0:
                versioned_name = f"{base_name} [{src_path.stem}]"
            else:
                versioned_name = base_name
            workflow = sanitize_workflow(source, src_path, raw, force_name=versioned_name)
        except Exception as exc:
            skipped += 1
            manifest.append(
                {
                    "source": source,
                    "input": str(src_path.relative_to(ROOT)),
                    "status": "skipped",
                    "reason": str(exc),
                }
            )
            continue

        out_name = f"{slugify(workflow['name'])}__{slugify(src_path.stem)}.json"
        out_path = OUT_DIR / out_name
        out_path.write_text(
            json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written += 1

        manifest.append(
            {
                "source": source,
                "input": str(src_path.relative_to(ROOT)),
                "output": str(out_path.relative_to(ROOT)),
                "status": "ok",
                "workflow_name": workflow["name"],
                "node_count": len(workflow["nodes"]),
            }
        )

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "written": written,
                "skipped": skipped,
                "items": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Workflows fusionados: {written} | Saltados: {skipped}")
    print(f"Manifest: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
