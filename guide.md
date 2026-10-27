# Pass-The-Mic: setup guide

A **voice agent** is a character that writes a reply and reads it aloud. One laptop runs the **moderator**, which introduces the topic and gives each character a turn.

The laptops connect over Wi-Fi using **WebSocket**, a connection for exchanging messages. Each laptop plays its own audio. No SSH or microphone is needed.

## 1. Prepare every laptop

You need Python, this project, speakers, internet access, and the same Wi-Fi network. Everyone should use the same project version.

Open a terminal in the **project folder**: the folder containing `requirements.txt`. On Windows, right-click inside that folder and choose **Open in Terminal** (PowerShell).

Run these commands one at a time:

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

A **virtual environment** keeps this project's tools together. In each new terminal, open the project folder and repeat only the activation command.

If Windows blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` in the commands below. If Python is missing, install it before continuing.

## 2. Check the speakers — everyone

All commands below run from the project folder.

```bash
python character_agents/test_local_voice.py --preset orange_optimist.json
```

You should hear a greeting. Check volume, audio output, and internet access if you do not. Test the host too: the moderator speaks from its speakers.

## 3. Start the moderator — host only

```bash
python -m moderator.server
```

Leave the terminal open. Find the printed address:

```text
Local LAN IP: 192.168.1.42:8000
```

The **IP address** identifies the host laptop; `8000` is the app's connection port. Share your actual IP with participants. The address above is an example.

Allow Python through the host's firewall on your private network, using port `8000`. Open `http://localhost:8000` on the host to see the connected characters.

## 4. Connect two characters — participants

Start with the included characters. Replace the example IP with the host's actual IP.

**Participant 1: Team Orange**

```bash
python character_agents/run_my_agent.py --preset orange_optimist.json --host 192.168.1.42 --provider mock
```

**Participant 2: Team Red**

```bash
python character_agents/run_my_agent.py --preset red_skeptic.json --host 192.168.1.42 --provider mock
```

`mock` uses ready-made replies for the first test. It needs no AI key, but voice generation still needs internet.

Wait for **Registration confirmed by Host!** Leave both terminals open. The host should refresh its browser page and check that both teams appear.

**Only two laptops?** Run Team Orange in another terminal on the host, using `--host 127.0.0.1`. Run Team Red on the other laptop using the host's Wi-Fi IP. Activate the environment in the new terminal first.

## 5. Start the conversation — host only

Open another terminal. Keep the moderator running.

**Windows PowerShell**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/start -ContentType 'application/json' -Body '{"max_turns":6}'
```

**macOS / Linux**

```bash
curl -X POST http://localhost:8000/start -H 'Content-Type: application/json' -d '{"max_turns":6}'
```

The moderator introduces the topic. The characters speak and pass the mic between laptops. After **six total character turns**, the moderator closes the conversation.

Keep laptops awake. When both characters have spoken, your connection test is complete.

## 6. Enable AI-generated replies — each participant

An **API key** is a private access code for an AI service.

1. Get a key from your Groq account.
2. Copy `.env.example` to `.env` in the project folder. If `.env` exists, edit it instead.
3. Replace the placeholder on the `GROQ_API_KEY=` line with your key, then save.
4. Stop your character with `Ctrl+C`. Restart it without `--provider mock`:

```bash
python character_agents/run_my_agent.py --preset orange_optimist.json --host 192.168.1.42
```

Use your own preset and the host's IP. Check that the displayed provider says **GROQ**. Once everyone reconnects, repeat Step 5.

Each participant configures their own key. Keep keys private. Failed AI requests can fall back to ready-made replies; check terminal errors if that happens.

## 7. Create your own character — optional

Stop your character, then run:

```bash
python character_agents/create_agent.py
```

Answer the questions. A **persona** is your character's personality; a **secret mission** is its playful goal. The program prints the saved filename, such as `priya.json`.

Use different names for every participant. Then test and connect:

```bash
python character_agents/test_local_voice.py --preset priya.json
python character_agents/run_my_agent.py --preset priya.json --host 192.168.1.42
```

Replace the filename and IP with yours.

Current limits: recreating the same filename overwrites it; team-color names can override your voice selection. Use names such as Priya or Sam and back up existing profiles. Missions are excluded from public profiles but sent to your AI provider; do not enter sensitive information.

## Stop or play again

After a conversation finishes, repeat Step 5 to play again. To request an early stop:

**Windows PowerShell**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/stop
```

**macOS / Linux**

```bash
curl -X POST http://localhost:8000/stop
```

Wait for any ongoing speech and closing remarks to finish before restarting. At the end, press `Ctrl+C` in the character and moderator terminals.

## Quick fixes

| Problem | Check |
| --- | --- |
| Cannot connect | Correct host IP, same Wi-Fi, running moderator, and host firewall allowing port `8000`. Guest Wi-Fi may block laptop-to-laptop connections. |
| Missing character | Every character needs a unique name and a registration confirmation. |
| No sound | Repeat Step 2; check speakers and internet access. |
| Ready-made replies | Remove `--provider mock`, check `.env`, restart the character, and read any provider errors. |
| Missing Python module | Activate the environment and repeat the install command in Step 1. |
| Skipped turn or overlapping voices | The host waits 45 seconds for each turn; slow AI requests or long speech can exceed this. |

## Optional technical details

- **Connection:** the app automatically opens `ws://HOST_IP:8000/ws`. It exchanges turn instructions, history, public profiles, and replies. Audio stays on each laptop.
- **Topics:** view `http://localhost:8000/topics` on the host. Edit `moderator/topics.json` to change topics and spoken introductions, then restart the server and reconnect agents. Update team names in the introduction when using custom characters.
- **Choose an opener:** the start request also accepts `topic_id` and `first_speaker`, for example `{"topic_id":"open-source-vs-closed","first_speaker":"Priya","max_turns":6}`. Use an existing topic ID and a connected character's exact name.
- **OpenAI instead:** set `OPENAI_API_KEY` in `.env` and leave the Groq key empty or at its placeholder. Groq takes priority when both keys are usable.
- **Moderator:** introductions and closing remarks are scripted. AI-generated replies come from the character agents.
- **Network:** use a trusted local network. The server has no login or encryption; do not expose port `8000` to the internet.

Commands checked against the code. Live multi-laptop conversation, AI requests, and audio playback have not been tested here.
