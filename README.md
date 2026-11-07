# pass-the-mic: multi-agent voice roundtable

A Python project for running an in-person, multi-agent voice debate across laptops on a local Wi-Fi network. One laptop runs the moderator and a WebSocket coordinator. Each participant runs a character agent on their own machine. When an agent gets the mic, it writes a short reply, speaks it through its own speakers with Edge TTS, and names the next speaker.

This repository is a fork of [Chandukasireddy/pass-the-mic](https://github.com/Chandukasireddy/pass-the-mic). The original project and its design are the upstream author's work.

## Upstream and my contributions

- Upstream: [Chandukasireddy/pass-the-mic](https://github.com/Chandukasireddy/pass-the-mic)
- My work in this fork: [commit 2c5fa17](https://github.com/rahuloruganti/pass-the-mic/commit/2c5fa1767db7a323770c07beeddd4c2b85c0f118), whose subject is "add create_agent script and guide, rework agent builder, LLM and protocol, update tests".

That commit covers:

- `character_agents/create_agent.py` (new): an interactive preset builder that asks for a name, persona, interests, speaking style, catchphrase, private mission, and voice, then writes `character_agents/presets/<name>.json`.
- `character_agents/agent_builder.py`: three new preset fields (`about`, `catchphrase`, `secret_mission`), a public `blurb` that excludes the secret mission, a private `persona_prompt` that includes it, a `peers` argument threaded through turn generation, and a `from_preset` that merges preset data with constructor overrides (`cls(**{**data, **overrides})`) so any field, including `llm_client`, can be overridden.
- `core/llm.py`: the system prompt now lists the other participants by name with their public blurbs and asks the agent to react to them; the `peers` map is passed through both the sync and async turn-generation paths.
- `core/protocol.py`: a `peers` field on the `TurnGrant` model.
- `moderator/server.py` and `simulate_roundtable.py`: one-line changes that attach each eligible peer's public blurb to the turn grant.
- `guide.md` (new): a step-by-step setup guide for a host and two participant laptops.
- `tests/test_roundtable.py`: one new test, `test_profile_fields_and_peer_awareness`, covering override merging, blurb privacy, and the peer block in the system prompt.
- `character_agents/README.md`: documents the question-driven preset flow and the new profile fields.

The rest of the project is upstream work. The coordinator, the `CharacterAgent` base class, the tolerant parser, provider selection, and the pre-existing tests were already there; this commit edits those files but does not introduce those components.

The fork keeps the upstream architecture: a FastAPI coordinator, a moderator voice agent, and per-laptop character agents.

```text
┌──────────────────────┐                 ┌──────────────────────┐
│   HOST / MODERATOR   │                 │      TEAM ORANGE     │
│  coordinator + WS    │◄───────────────►│  LLM + Edge TTS      │
└──────────┬───────────┘                 └──────────┬───────────┘
           │                                        │
           │  WebSocket over local Wi-Fi            │ speaks, then
           │  turn grants and mic passes            │ passes the mic
           ▼                                        ▼
┌───────────────────────────────────────────────────────────────┐
│                  FastAPI coordinator on port 8000             │
└───────────────────────────────────────────────────────────────┘
```

## Repository layout

- `core/`: shared LLM client, Edge TTS wrapper, pygame playback, and the turn protocol.
- `moderator/`: FastAPI and WebSocket server, moderator agent, terminal dashboard, and topics.
- `character_agents/`: attendee agent class, guided preset creator, runner, local voice test, and example presets.
- `simulate_roundtable.py`: one-laptop simulation with a moderator and two or three characters.
- `tests/`: unit and integration tests.
- `guide.md`: host and participant walkthrough, including Windows commands and troubleshooting.

## Quickstart

Install dependencies once per machine:

```bash
git clone https://github.com/rahuloruganti/pass-the-mic.git
cd pass-the-mic
pip install -r requirements.txt
```

### Simulate on one laptop

```bash
python simulate_roundtable.py --provider mock --rounds 3
python simulate_roundtable.py --mute --rounds 2
```

`--provider mock` uses ready-made replies, so the first run needs no API key and makes no provider call. Without that flag, `core/llm.py` picks up a Groq or OpenAI key from `.env` if one is set and sends real requests to that provider. `--mute` skips playback for a faster text-only check, and `--three-teams` adds a third character.

### Host a room

```bash
python -m moderator.server
```

The server prints a LAN address such as `192.168.1.42:8000` and serves a status page at `http://localhost:8000`. Start a debate with:

```bash
curl -X POST http://localhost:8000/start -H "Content-Type: application/json" -d '{"max_turns": 6}'
```

The start request also accepts `topic_id` and `first_speaker`. Topics are listed at `/topics` and stored in `moderator/topics.json`.

### Join as a participant

```bash
cd character_agents
python create_agent.py
python test_local_voice.py --preset presets/orange_optimist.json
python run_my_agent.py --preset presets/orange_optimist.json --host 192.168.1.42
```

`create_agent.py` is optional; the four presets in `character_agents/presets/` work as examples. Participants should use distinct names and agree on the same project version as the host. See [`character_agents/README.md`](character_agents/README.md) and the full [`guide.md`](guide.md) for setup and troubleshooting.

## Voice and audio

`core/tts.py` uses Microsoft Edge neural voices through `edge-tts`. It needs no API key or subscription, but it does need internet access: synthesis calls a Microsoft endpoint, so availability and latency depend on that service and the local network. Audio is written to a temporary MP3 and played with pygame. Playback can block so that one laptop does not talk over another.

| Team | Voice | Accent |
| :--- | :--- | :--- |
| Moderator | `en-US-GuyNeural` | US English |
| Team Orange | `en-US-AriaNeural` | US English |
| Team Red | `en-GB-RyanNeural` | British English |
| Team Blue | `en-AU-NatashaNeural` | Australian English |
| Team Emerald | `en-US-ChristopherNeural` | US English |
| Team Purple | `en-GB-SoniaNeural` | British English |
| Team Amber | `en-IN-NeerjaNeural` | Indian English |
| Team Silver | `en-US-JennyNeural` | US English |
| Team Onyx | `en-CA-LiamNeural` | Canadian English |

A team name containing a color can override a preset's voice choice. Use a personal name if you want to keep the selected voice.

## LLM providers

`core/llm.py` chooses a provider in this order:

1. Groq, when a usable `GROQ_API_KEY` is set. The default model is `llama-3.3-70b-versatile`.
2. OpenAI, when a usable `OPENAI_API_KEY` is set and Groq is not configured. The default model is `gpt-4o-mini`.
3. Mock mode, when neither usable key is present.

Mock mode returns canned, topic-aware replies so the room can test turn-taking without an AI key. It is not a live model. With a real provider, latency depends on the provider, model, and network; the project does not claim a response-time target. Copy `.env.example` to `.env` and add your own key. Each participant uses their own key.

## Turn protocol

Every agent returns one JSON object:

```json
{
  "speaker": "Team Orange",
  "spoken_text": "Open weights are moving quickly. Passing the mic to Team Red to hear the safety case.",
  "next_agent": "Team Red"
}
```

The host sends a `your_turn` message containing the topic, recent history, eligible peers, round number, and a suggested time limit. The attendee replies with `turn_complete` and the turn object. `core/protocol.py` extracts JSON from prose or fenced blocks, retries after simple repairs, fills missing fields, and replaces an invalid or self-directed `next_agent` with an eligible peer. This keeps the round moving, though it cannot make a nonsensical model reply meaningful.

## Resilience and limits

- If a turn does not arrive within 45 seconds, the coordinator logs a timeout and has the moderator intervene before passing the mic on.
- If no participants remain connected, the roundtable stops.
- Self-passes are redirected to another connected agent.
- There is no login or transport encryption. Use a trusted local network and do not expose port 8000 to the internet.
- Multi-laptop operation, provider calls, and audio playback are not exercised by the test suite. `guide.md` states that these were not tested when it was written.
- The fork has no `LICENSE` file. Check the upstream repository's licensing before reuse.

## Tests

```bash
pytest
```

The tests use FastAPI's `TestClient` and the mock provider. They cover protocol serialization, parser recovery, voice mapping, presets, profile privacy, mock turn generation, and the REST endpoints. They do not start a real server, call an LLM, or play audio.
