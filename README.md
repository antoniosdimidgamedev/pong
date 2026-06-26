# Pong

Classic Pong for the terminal. Singleplayer on one keyboard or multiplayer over LAN with room-based matchmaking. No dependencies beyond Python 3.6+ and curses. Runs on Linux, macOS, and Termux.

## Features

- **Singleplayer mode** — two players share one keyboard (W/S vs arrow keys)
- **LAN multiplayer** — built-in TCP server with automatic IP detection
- **Room system** — browse active games or create your own with a generated name
- **Terminal UI** — full curses interface with menus, IP input, and a room selector
- **Diagnostics** — OS, kernel, architecture, and Python version shown at the bottom of every menu
- **Portable** — pure Python, no pip installs, works wherever Python and curses do

## Quick start

```bash
git clone https://github.com/YOUR_USER/pong.git
cd pong
python3 pong.py
```

Or download `pong.py` and run it directly — that is the entire game.

## How to play

### Menu

```
 Pong                      Play                      Multiplayer
  > Play              >     Singleplayer            > Host Server
    How to Play             Multiplayer >              Join Server
    Quit
```

Use arrow keys to navigate, Enter to select, Q or Esc to go back.

### Controls

| Player | Paddle up | Paddle down | Quit |
|---|---|---|---|
| Left (W/S) | `W` | `S` | `Q` |
| Right (arrows) | `↑` | `↓` | `Q` |

### Rules

First to 5 points wins. The ball speeds up slightly to keep rallies interesting. After a point the ball resets to center and launches toward the player who was scored on.

## LAN multiplayer

No internet required. Works over any local network (Wi-Fi, Ethernet, mobile hotspot).

### Host

1. Run `python3 pong.py`
2. Select **Play > Multiplayer > Host Server**
3. (Optional) Press `p` to change the port — default is 9999
4. Press `s` to start the server
5. Share the displayed IP address with the other player

The server runs in the terminal and accepts connections until you press Ctrl+C.

### Join

1. Run `python3 pong.py`
2. Select **Play > Multiplayer > Join Server**
3. Enter the host's IP address
4. A room browser appears — pick an open room or select **[New Game]** to create one
5. The match starts automatically once both players are in the same room

### Rooms

Rooms let multiple pairs play on the same server. Each room holds up to 2 players. When browsing, rooms show their player count (`0/2`, `1/2`) or `FULL`. Selecting **[New Game]** generates a random room name (e.g. `room_4821`).

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
        └── core.py        # the entire game
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

- **Protocol:** line-delimited JSON over TCP
- **Server threads:** one accept thread, one handler per client, one game loop per room
- **Game state:** simulated server-side; clients send key presses and receive state snapshots at ~25 fps
- **Curses:** uses `curses.color_pair`, `nodelay`, and `getch` for non-blocking input

## License

MIT. Do whatever you want with it.
