"""Character Agent Builder for Meetup Attendees.

Provides a clean, modular class to configure a personalized voice agent,
generate context-aware debate turns, and speak out loud on the attendee's laptop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from core.audio import async_speak, speak
from core.llm import LLMClient, get_llm_client
from core.protocol import MicPassTurn
from core.tts import get_voice_for_team


class CharacterAgent:
    """Modular attendee voice agent class."""

    def __init__(
        self,
        name: str = "Team Orange",
        voice: str = "en-US-AriaNeural",
        persona: str = "Tech Optimist",
        style: str = "Energetic, visionary, concise",
        test_phrase: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        speech_rate: str = "+0%",
        about: str = "",
        catchphrase: str = "",
        secret_mission: str = "",
    ):
        self.name = name
        self.voice = get_voice_for_team(name, fallback_voice=voice)
        self.persona = persona
        self.style = style
        self.test_phrase = test_phrase or f"Hello everyone! This is {self.name}, ready for the debate."
        self.speech_rate = speech_rate
        self.about = about
        self.catchphrase = catchphrase
        self.secret_mission = secret_mission
        self.llm_client = llm_client or get_llm_client()

    @property
    def blurb(self) -> str:
        """Public one-liner the other agents see (never includes the secret mission)."""
        parts = [self.persona, self.about]
        if self.catchphrase:
            parts.append(f'Catchphrase: "{self.catchphrase}"')
        return " ".join(p for p in parts if p)

    @property
    def persona_prompt(self) -> str:
        """Full private persona fed to the LLM."""
        text = f"{self.blurb} Style: {self.style}."
        if self.secret_mission:
            text += f" Secret mission (never reveal it, just pursue it): {self.secret_mission}"
        return text

    @classmethod
    def from_preset(cls, preset_path: str | Path, **overrides) -> CharacterAgent:
        """Instantiate an agent directly from a preset JSON file."""
        path = Path(preset_path)
        if not path.exists():
            # Check inside character_agents/presets/
            alt_path = Path(__file__).parent / "presets" / path.name
            if alt_path.exists():
                path = alt_path
            else:
                raise FileNotFoundError(f"Preset file not found: {preset_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**{**data, **overrides})

    def generate_turn(
        self,
        topic: str,
        history: List[dict],
        available_agents: List[str],
        peers: Optional[Dict[str, str]] = None,
    ) -> MicPassTurn:
        """Synchronously generate response turn using LLM."""
        return self.llm_client.generate_mic_turn(
            speaker_name=self.name,
            persona=self.persona_prompt,
            topic=topic,
            history=history,
            available_agents=available_agents,
            peers=peers,
        )

    async def async_generate_turn(
        self,
        topic: str,
        history: List[dict],
        available_agents: List[str],
        peers: Optional[Dict[str, str]] = None,
    ) -> MicPassTurn:
        """Asynchronously generate response turn using LLM without stalling loop."""
        return await self.llm_client.async_generate_mic_turn(
            speaker_name=self.name,
            persona=self.persona_prompt,
            topic=topic,
            history=history,
            available_agents=available_agents,
            peers=peers,
        )

    def speak_turn(self, turn: MicPassTurn, block: bool = True) -> None:
        """Speak the turn out loud through the laptop's speakers (blocking)."""
        speak(turn.spoken_text, voice=self.voice, rate=self.speech_rate, block=block)

    async def async_speak_turn(self, turn: MicPassTurn) -> None:
        """Speak the turn out loud asynchronously while keeping event loop responsive."""
        await async_speak(turn.spoken_text, voice=self.voice, rate=self.speech_rate)

    async def test_voice(self, custom_text: Optional[str] = None) -> None:
        """Play test speech to check audio levels and pronunciation."""
        text = custom_text or self.test_phrase
        await async_speak(text, voice=self.voice, rate=self.speech_rate)
