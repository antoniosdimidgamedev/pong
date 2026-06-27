# Web Dashboard

The web dashboard lets you monitor your Pong server from any browser on the same network — no extra setup, no web frameworks, just pure Python stdlib.

## Starting the Dashboard

The dashboard starts automatically when you host a server. You'll be prompted for the port (default **8080**). The server management screen shows the URL:

```
Web: http://192.168.1.42:8080/
```

Open that URL in any browser to see live game status.

## Pages

### Status JSON (`/status`)

Returns raw JSON with all server information:

```json
{
  "server": {
    "name": "My Server",
    "ip": "192.168.1.42",
    "port": 5555,
    "uptime": "01:23:45"
  },
  "rooms": [
    {
      "name": "Arcade",
      "players": 2,
      "full": true,
      "playing": true,
      "player_names": ["Alice", "Bob"],
      "player_sides": ["left", "right"],
      "left_score": 3,
      "right_score": 2,
      "uptime": "00:12:34"
    }
  ],
  "events": [
    {"time": "12:34:56", "msg": "Alice joined room Arcade"},
    {"time": "12:35:10", "msg": "Bob joined room Arcade"},
    {"time": "12:35:11", "msg": "Game started in Arcade"}
  ]
}
```

### HTML Dashboard (`/`)

A self-contained HTML page that auto-refreshes every 2 seconds and displays:

- Server name, IP, port, web URL, and uptime
- Room list with status badges (Open / Full / Playing)
- Player names and current scores for each room
- Live event log with timestamps

## Implementation

The dashboard uses Python's built-in `http.server.HTTPServer` and serves both the JSON API and a pre-rendered HTML page. It runs in a separate daemon thread and has no effect on game performance.
