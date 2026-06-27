# Pong

Classic Pong for the terminal. Player vs CPU with three difficulty levels, local two-player on one keyboard, or multiplayer over LAN with room-based matchmaking, in-game chat, a web dashboard, and automatic server discovery. No dependencies beyond Python 3.6+ and curses. Runs on Linux, macOS, and Termux.

## Features

- **Player vs CPU** — three difficulty levels (Easy, Medium, Hard) with adaptive AI that tracks the ball, reacts with human-like delay, and has configurable paddle speed and accuracy
- **Save / Load** — press `S` during a CPU game to save your progress to `~/.pong/save.json`; resume later from **Play > Singleplayer > Load Game**
- **Local two-player** — two players share one keyboard (W/S vs arrow keys)
- **LAN multiplayer** — built-in TCP server with automatic IP detection, UDP broadcast discovery, and a server browser
- **Room templates** — pick from 10 preset room names (Classic, Rally, Speed, Tournament, Practice, Sudden Death, Challenge, Arena, Grand Slam, Showdown) or create a new one
- **Web dashboard** — live HTTP dashboard showing server status, active rooms with scores and player names, and recent events; viewable from any browser on the LAN
- **Server management screen** — when hosting, a curses interface shows rooms, connected players, live scores, and a real-time event log; hosts can join their own games locally
- **Kick players** — from the host screen, press Enter on a room to see its players, navigate to a player, and press `k` to kick them
- **Custom player names** — prompted on join; displayed in-game, in chat, in the management screen, and in the web dashboard
- **Custom server names** — configure a name before starting; broadcast in UDP discovery and shown in the server browser
- **In-game chat** — press `/` to open chat input, type your message, press Enter to send, Esc to cancel
- **Chat history** — last 100 messages stored server-side and sent to late-joining players
- **Chat filter** — common profanity is automatically censored server-side before reaching other players
- **Terminal UI** — full curses interface with menus, IP input, a room selector, and a server browser with auto-discovery
- **Diagnostics** — OS, kernel, architecture, and Python version shown at the bottom of every menu
- **Portable** — pure Python, no pip installs, works wherever Python and curses do
- **PyPI package** — install with `pip install terminal-pong` and run with the `pong` command

## Quick start

```bash
git clone https://github.com/antoniosdimidgamedev/pong.git
cd pong
python3 pong.py
```

Or install from PyPI and run from anywhere:

```bash
pip install terminal-pong
pong
```

## How to play

### Menu

```
 Pong                         Play                              Singleplayer
  > Play                 >     Singleplayer >              >      New Game >
    How to Play                Multiplayer >                      Load Game      (if save exists)
    Quit                                                          Player vs CPU >
                                                                   Easy / Medium / Hard
                                                                  Player vs Player
```

Use arrow keys to navigate, Enter to select, Q or Esc to go back.

### Controls

| Mode | Player | Paddle up | Paddle down | Special | Quit |
|---|---|---|---|---|---|
| Two-player | Left (W/S) | `W` | `S` | — | `Q` |
| Two-player | Right (arrows) | `↑` | `↓` | — | `Q` |
| vs CPU | You (W/S) | `W` | `S` | `S` save | `Q` |
| Multiplayer | Left (W/S) | `W` | `S` | `/` chat | `Q` |
| Multiplayer | Right (arrows) | `↑` | `↓` | `/` chat | `Q` |

### Rules

First to 5 points wins. After a point the ball resets to center and launches toward the player who was scored on.

### Chat (Multiplayer only)

Press `/` to enter chat mode. The prompt appears at the bottom of the screen. Type your message and press Enter to send. Press Esc to cancel. Chat messages from both players are shown in the bottom few lines of the game screen. If you join a room with existing chat history, the last 100 messages are replayed to you.

### Save / Load (CPU only)

Press `S` during a CPU game to save your progress. The current score, paddle positions, ball state, and difficulty are written to `~/.pong/save.json`. On the next launch, select **Play > Singleplayer > Load Game** to resume. The save is erased automatically when the game ends (someone wins) or can be discarded by starting a fresh game.

## Player vs CPU

Select **Play > Player vs CPU** then choose a difficulty:

- **Easy** — slow paddle, delayed reactions, frequently misses. Good for beginners.
- **Medium** — moderate tracking speed, occasional jitter. A fair opponent.
- **Hard** — fast paddle, minimal delay, tracks the ball tightly. Difficult to beat.

The CPU paddle only chases the ball when it is moving toward it. When the ball moves away, the CPU drifts back to center. This makes the AI feel more natural and less robotic.

## LAN multiplayer

No internet required. Works over any local network (Wi-Fi, Ethernet, mobile hotspot).

### Host

1. Run `python3 pong.py`
2. Select **Play > Multiplayer > Host Server**
3. Configure your server:
   - `p` — change the game port (default 9999)
   - `n` — set a custom server name (defaults to your hostname)
   - `w` — set the web dashboard port (default 8080)
4. Press `s` to start
5. Share the displayed IP address, or let other players find your server via automatic discovery

The management screen shows active rooms, connected players, live scores, and a real-time event log:

```
 Pong — Server: My Server
 IP: 192.168.1.100:9999   Web: http://192.168.1.100:8080   Uptime: 0h 2m 34s

 Active Rooms:
   > Classic  (2/2 PLAYING)  2-3  [Alice, Bob]
     Rally    (1/2)  [Charlie]

 Recent Events:
   [10:32] Room 'Classic' created
   [10:33] Alice (left) joined 'Classic'
   [10:34] Bob (right) joined 'Classic'

 j  join locally   k  kick player   q  stop server
```

From here you can:
- Press `j` to join your own server as a local client — play on 127.0.0.1, then return to the management screen when the game ends
- Press Enter on a room to see its player list, navigate with arrows, and press `k` to kick a player
- Press `q` to stop the server and go back to the menu

### Join

1. Run `python3 pong.py`
2. Select **Play > Multiplayer > Join Server**
3. An auto-discovery screen scans the LAN for servers broadcasting on UDP port 10000
4. Pick a detected server or select **[Enter IP Manually]** to type an address
5. Enter your display name when prompted
6. A room browser appears — pick an open room, a template name, or select **[New Game]** to create one
7. The match starts automatically once both players are in the same room

### Rooms

Rooms let multiple pairs play on the same server. Each room holds up to 2 players. When browsing, active rooms show their player count (`0/2`, `1/2`) or `FULL`. The room selector also shows 10 template names you can pick from to quickly start a themed game. Selecting **[New Game]** generates a random room name.

### Server browser

When joining, the server browser listens for UDP broadcast packets on port 10000. Any pong server on the LAN sends an announcement every 3 seconds containing its IP, port, and name. Detected servers appear in a list with live updates. Press `r` to rescan.

## Web dashboard

When hosting, pong starts a lightweight HTTP server that serves a live dashboard:

```
http://<server-ip>:8080
```

The dashboard shows:
- Server name, IP, and game port
- Uptime and total player count
- A table of active rooms showing status (waiting / playing / full), player names, current score, and room uptime
- An event log with timestamps

The page auto-refreshes every 2 seconds via a `/status` JSON endpoint. No external web server or dependencies needed — it is built into the game.

## Files

```
pong/
├── pong.py              # entry point (just launches src/pong/core.py)
├── pyproject.toml        # PyPI build config (pip install terminal-pong)
├── LICENSE
├── README.md
├── setup.sh              # dependency checker
├── description.txt       # short GitHub description
└── src/
    └── pong/
        ├── __init__.py    # exports main()
        ├── __main__.py    # python -m pong support
        └── core.py        # the entire game (~1500 lines)
```

Everything lives in one Python file (`src/pong/core.py`). The root `pong.py` is a tiny launcher. `setup.sh` is optional.

## Requirements

- **Python 3.6+** — check with `python3 --version`
- **curses** — built into Python on Linux, macOS, and Termux

### Termux

```bash
pkg install python ncurses
python3 pong.py
```

### Linux / macOS

curses ships with the system Python. No extra setup needed.

```bash
python3 pong.py
```

## Setup script

```bash
chmod +x setup.sh
./setup.sh
```

Checks Python version, curses availability, and terminal size, then prints instructions.

## Technical details

- **Protocol:** line-delimited JSON over TCP (one JSON object per line, terminated by `\n`)
- **Server threads:** one accept thread, one handler per client, one game loop per room, one UDP broadcaster, one HTTP dashboard server
- **Discovery:** UDP broadcast on port 10000 every 3 seconds; clients listen on the same port and collect announced servers
- **Game state:** simulated server-side; clients send key presses and receive state snapshots at ~25 fps
- **Curses:** uses `curses.color_pair`, `nodelay`, and `getch` for non-blocking input
- **Chat:** triggered by `/` key, messages relayed through server, filtered for profanity, history capped at 100 messages
- **Web dashboard:** pure stdlib `http.server.HTTPServer` with a JSON status endpoint and an auto-refreshing HTML page showing status badges, scores, and player names
- **CPU AI:** each tick the AI evaluates ball position and direction, applies difficulty-based reaction threshold and jitter, then emits the appropriate up/down keys
- **Save system:** serializes `GameState` fields plus mode and difficulty to `~/.pong/save.json`; only available in CPU mode
- **Synchronization:** shared state protected by `threading.Lock`; server accepts connections while game loops run independently per room

## License

MIT. Do whatever you want with it.
