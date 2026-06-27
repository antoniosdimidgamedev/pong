# Architecture

The entire game is contained in a single file (`src/pong/core.py`, ~1800 lines). Here's how it's organized.

## File Structure

```
pong/
├── pong.py              # Entry point — adds src/ to path, runs core.main()
├── setup.sh             # Dependency checker
├── SHA256SUMS           # File integrity hash
├── README.md            # Full documentation
└── src/
    └── pong/
        ├── __init__.py  # Empty package init
        └── core.py      # Everything else
```

## Thread Model

```
┌─────────────────────────────────────────────────┐
│                   main thread                    │
│           curses.wrapper(main_menu)              │
│         (blocking getch, menu navigation)        │
└─────────────────────┬───────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌─────────────────┐     ┌─────────────────────┐
│  Server Mode    │     │   Client Mode       │
│  (host server)  │     │   (join server)     │
│                 │     │                     │
│ ┌─────────────┐ │     │ ┌─────────────────┐ │
│ │ Server      │ │     │ │ game_loop()     │ │
│ │ acceptor    │ │     │ │ (pump + render) │ │
│ │ thread      │ │     │ └─────────────────┘ │
│ └─────────────┘ │     └─────────────────────┘
│ ┌─────────────┐ │
│ │ Room        │ │
│ │ game loops  │ │
│ │ (one/room)  │ │
│ └─────────────┘ │
│ ┌─────────────┐ │
│ │ Web         │ │
│ │ dashboard   │ │
│ │ thread      │ │
│ └─────────────┘ │
│ ┌─────────────┐ │
│ │ UDP         │ │
│ │ announcer   │ │
│ │ thread      │ │
│ └─────────────┘ │
└─────────────────┘
```

## Key Components

### GameState (`core.py:119`)

The core game logic — a stateless(ish) data object that holds paddle positions, ball position/velocity, and scores. `update()` applies inputs and physics for one tick. Pure data — no I/O.

### Menu System (`core.py:1003-1200`)

Curses-based menus with `draw_menu()` and `menu_loop()`. Menus use a `dirty` flag pattern to avoid flicker — only redraw when input changes. Submenus nest naturally since `menu_loop()` returns the selected index or `-1` for back.

### Server (`core.py:475-820`)

Multi-threaded TCP server:
- **Acceptor thread** accepts new connections
- **Room game loop threads** run at 25 fps, calling `GameState.update()` and broadcasting state
- **Handler threads** per connection read JSON messages and update room input sets
- **UDP announcer** broadcasts server presence on port 10000
- **Web dashboard** runs in a separate daemon thread

### Client (`core.py:822-1000`)

Connects via TCP to the server, receives game state, and renders it locally. The `pump()` function handles non-blocking socket reads in the main game loop.

### CPU AI (`core.py:350-372`)

Simple parameterized ball-chaser. Three difficulty levels control threshold, speed, and jitter.

## Data Flow

```
── Local Game ──
Input → GameState.update() → render()

── Multiplayer (Server Side) ──
Client input → Room handler → input sets → GameState.update() → state broadcast

── Multiplayer (Client Side) ──
Server state → pump() → render()

── Web Dashboard ──
Server lock → read rooms/events → JSON/HTML response
```
