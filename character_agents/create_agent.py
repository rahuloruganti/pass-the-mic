"""Build your own character agent by answering a few questions.

Writes presets/<your-name>.json, ready for test_local_voice.py and run_my_agent.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.tts import VOICE_REGISTRY

PRESETS = Path(__file__).parent / "presets"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{prompt}{suffix}: ").strip() or default


def main() -> None:
    print("\nBuild your agent. It speaks for YOU at the table, so make it sound like you.\n")
    name = ask("Your name or team name", "Team Mystery")
    persona = ask("Who are you in one line? (e.g. 'Coffee-obsessed backend engineer')")
    about = ask("What are you into / what are your hot takes?")
    style = ask("How do you talk? (e.g. 'dry, sarcastic, rambles about trains')", "Friendly, witty, concise")
    catchphrase = ask("Your catchphrase (optional)")
    secret_mission = ask("Secret mission for the table, kept private (e.g. 'get everyone to agree pineapple belongs on pizza')")

    voices = [(team, meta["voice_id"]) for team, meta in VOICE_REGISTRY.items()]
    for i, (team, voice_id) in enumerate(voices, 1):
        print(f"  {i}. {voice_id:<26} ({VOICE_REGISTRY[team]['accent']})")
    pick = ask("Pick a voice number", "1")
    voice = voices[int(pick) - 1][1] if pick.isdigit() and 1 <= int(pick) <= len(voices) else voices[0][1]

    profile = {
        "name": name,
        "voice": voice,
        "persona": persona or "Curious participant",
        "about": about,
        "style": style,
        "catchphrase": catchphrase,
        "secret_mission": secret_mission,
        "test_phrase": f"Hi everyone, {name} here. {catchphrase}".strip(),
    }

    PRESETS.mkdir(exist_ok=True)
    path = PRESETS / f"{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_') or 'agent'}.json"
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nSaved {path}")
    print(f"Hear it:    python test_local_voice.py --preset {path.name}")
    print(f"Join game:  python run_my_agent.py --preset {path.name} --host <host-ip>")


if __name__ == "__main__":
    main()
