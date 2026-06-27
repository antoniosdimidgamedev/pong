# LAN Multiplayer

The game includes a built-in LAN multiplayer system — no external servers, no port forwarding (within a LAN). One player hosts a server, others join.

## How It Works

1. **Host** starts a server from the menu
2. Server broadcasts its presence via UDP every 3 seconds on port **10000**
3. **Joining players** scan the LAN and see all available servers
4. Player selects a server and a room (or creates one)
5. Game starts when both players are in the same room

## Hosting a Server

From the main menu:

```
Play > Multiplayer > Host Server
```

You'll be prompted for:
- **Server name** — visible to other players during discovery
- **Web dashboard port** — optional, for browser monitoring (default 8080)

After starting, the **Server Management Screen** appears showing live room status, connected players, and events.

## Joining a Server

From the main menu:

```
Play > Multiplayer > Join Server
```

The game scans the LAN for servers (takes ~2 seconds). Available servers appear in a list. Select one, then:

1. Enter your **player name**
2. Select a **room** from the list (or create a new one)
3. Wait for another player to join
4. The game starts automatically

## Room Templates

When creating a room, you can choose from 10 themed templates or create a custom-named room. Rooms appear in the selector with their current player count.

## Protocol

The game uses a simple JSON-over-TCP protocol:

**Client → Server:**
```json
{"type": "join", "room": "Room Name", "player_name": "Alice"}
{"type": "input", "keys": ["w", "s"]}
{"type": "list_rooms"}
{"type": "chat", "text": "hello"}
```

**Server → Client:**
```json
{"type": "assign", "player": "left", "name": "Alice", "opponent": "Bob"}
{"type": "state", "ball_x": 40, "ball_y": 12, "left_y": 5, ...}
{"type": "win", "winner": "left", "left_score": 5, "right_score": 3}
{"type": "chat", "from": "Alice", "text": "hello"}
{"type": "chat_history", "messages": [{"from": "Alice", "text": "hello"}, ...]}
{"type": "room_list", "rooms": [{"name": "Arcade", "players": 1}, ...]}
```

Server state is broadcast at **25 fps** (TICK = 0.04s). Clients send their current key set each frame.

## Server Discovery

- Hosts send UDP broadcast: `{"type":"pong_announce","port":...,"name":...}` every 3 seconds to port **10000**
- Clients listen for these broadcasts and display them in the server browser
- Each client scans for ~2 seconds before showing results
