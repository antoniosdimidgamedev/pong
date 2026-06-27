# Server Management

When you host a server, the **Server Management Screen** appears — a curses-based admin panel for monitoring and controlling your game server.

## Screen Layout

```
╔══════════════════════════════════════════════╗
║          Pong Server Management              ║
╠══════════════════════════════════════════════╣
║ IP: 192.168.1.42 | Port: 5555               ║
║ Web: http://192.168.1.42:8080/               ║
║ Uptime: 00:05:23                             ║
╠══════════════════════════════════════════════╣
║ Rooms                                        ║
║ ┌────────────────────────────────────────┐   ║
║ │ > Arcade  (2/2)  playing  3 - 2       │   ║
║ │   ├ Alice (left)                       │   ║
║ │   └ Bob   (right)                      │   ║
║ │   Lobby   (0/2)  waiting              │   ║
║ └────────────────────────────────────────┘   ║
║ Events                                       ║
║ 12:34:56  Alice joined room Arcade           ║
║ 12:35:10  Bob joined room Arcade             ║
║ 12:35:11  Game started in Arcade             ║
╠══════════════════════════════════════════════╣
║ ↑↓ navigate  Enter expand  j join  k kick   ║
╚══════════════════════════════════════════════╝
```

## Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate rooms and players |
| `Enter` | Expand/collapse room to show player list |
| `J` | **Join your own server** locally as a player |
| `K` | **Kick** the selected player from the room |
| `Q` / `Esc` | Shut down the server and return to menu |

## Features

### Room List

Shows all active rooms with:
- Room name
- Player count (e.g., `2/2`)
- Status: `waiting` or `playing`
- Current score (if playing)

### Player List

Press `Enter` on a room to expand it and see individual players, their side (left/right), and their connection status.

### Kick Player (`K`)

Select a player inside a room and press `K` to disconnect them. The server closes that player's socket, the handler thread detects the disconnect, and the room is updated. Useful for removing idle or disruptive players.

### Join Locally (`J`)

Press `J` to join your own server as a local player. This launches the game client using the same screen (`stdscr`), connecting to `127.0.0.1` on the server's port. After the game ends, you return to the management screen.

### Event Log

The bottom section shows a live log of server events (joins, leaves, game starts, scores) with timestamps.
