#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "config" / "personality_agent.json"
BITACORA_PATH = REPO_ROOT / "docs" / "BITACORA_PROYECTO.md"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def now_human() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        raise FileNotFoundError(f"No existe el perfil: {PROFILE_PATH}")
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def save_profile(data: dict) -> None:
    PROFILE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def ensure_bitacora() -> None:
    if BITACORA_PATH.exists():
        return
    BITACORA_PATH.write_text(
        (
            "# Bitacora De Proyecto - Lucy Fusion\n\n"
            "## Objetivo\n"
            "Registrar decisiones, cambios y estado operativo del proyecto para continuidad humana.\n\n"
            "## Entradas\n\n"
            "| Fecha | Cambio | Detalle | Estado |\n"
            "|---|---|---|---|\n"
        ),
        encoding="utf-8",
    )


def append_bitacora(cambio: str, detalle: str, estado: str) -> None:
    ensure_bitacora()
    line = f"| {now_human()} | {cambio} | {detalle} | {estado} |\n"
    with BITACORA_PATH.open("a", encoding="utf-8") as file:
        file.write(line)


def cmd_show(_: argparse.Namespace) -> int:
    profile = load_profile()
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    return 0


def cmd_add_note(args: argparse.Namespace) -> int:
    profile = load_profile()
    notes = profile.setdefault("notes", [])
    notes.append({"timestamp": now_iso(), "text": args.text})
    save_profile(profile)
    print("Nota agregada al perfil de personalidad.")
    return 0


def cmd_add_preference(args: argparse.Namespace) -> int:
    profile = load_profile()
    preferences = profile.setdefault("human_preferences", [])
    preferences.append(
        {
            "timestamp": now_iso(),
            "preference": args.preference,
        }
    )
    save_profile(profile)
    print("Preferencia humana registrada.")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    append_bitacora(args.cambio, args.detalle, args.estado)
    print("Entrada agregada a la bitacora.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agente local para memoria de personalidad y bitacora del proyecto."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show_parser = sub.add_parser("show", help="Mostrar perfil actual.")
    show_parser.set_defaults(func=cmd_show)

    note_parser = sub.add_parser("add-note", help="Agregar nota de personalidad.")
    note_parser.add_argument("--text", required=True, help="Texto de la nota.")
    note_parser.set_defaults(func=cmd_add_note)

    preference_parser = sub.add_parser(
        "add-preference", help="Registrar preferencia humana."
    )
    preference_parser.add_argument(
        "--preference", required=True, help="Preferencia a guardar."
    )
    preference_parser.set_defaults(func=cmd_add_preference)

    log_parser = sub.add_parser("log", help="Agregar entrada en la bitacora.")
    log_parser.add_argument("--cambio", required=True, help="Titulo del cambio.")
    log_parser.add_argument("--detalle", required=True, help="Detalle del cambio.")
    log_parser.add_argument(
        "--estado",
        default="hecho",
        choices=["hecho", "pendiente", "bloqueado"],
        help="Estado de la entrada.",
    )
    log_parser.set_defaults(func=cmd_log)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

