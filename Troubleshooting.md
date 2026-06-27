# Troubleshooting

## Common Issues

### `ImportError: No module named curses`

**Linux:** curses should be built into Python. Try `python3 -c "import curses"`. If it fails, install the dev package:

```bash
sudo apt install python3-dev ncurses-dev   # Debian/Ubuntu
sudo dnf install ncurses-devel             # Fedora
```

**macOS:** curses is included with the system Python and Homebrew Python. If missing, reinstall Python:

```bash
brew reinstall python3
```

**Termux:** curses requires a separate package:

```bash
pkg install ncurses
```

### `curses.error: setupterm: could not find terminal`

This usually happens over SSH or piped output. Set the TERM variable:

```bash
export TERM=xterm-256color
python3 pong.py
```

Or use a more capable terminal (iTerm2, GNOME Terminal, Termux, etc.).

### `[Errno 98] Address already in use` (hosting)

The default server port (5555) is already in use. Try a different port or kill the old process:

```bash
# Find and kill the old server
lsof -i :5555
kill <PID>

# Or use a different port (you'll be prompted)
```

### `Could not connect to host` (joining)

1. Make sure the host is running the server
2. Check that both machines are on the **same local network**
3. Check if a firewall is blocking port 5555 (or your custom port)
4. Try pinging the host machine
5. For wireless networks, check that client isolation / AP isolation is disabled

### No servers found (server browser)

1. Ensure the host server is running
2. Wait a few seconds — discovery takes ~2 seconds
3. Check that UDP port 10000 isn't blocked by a firewall
4. Some networks block broadcast traffic (corporate networks, public WiFi)
5. As a fallback, join manually by entering the host's IP address

### Web dashboard not loading

1. Verify the dashboard URL shown in the server management screen
2. Ensure you're on the same network as the server
3. Try `curl http://<server-ip>:8080/status` from the client machine
4. The dashboard port defaults to 8080 — check for port conflicts

### `Failed to get room list`

1. The server might be shutting down
2. Network connectivity issue — check the connection
3. Server version mismatch — ensure both sides use the same game version

### Game runs too fast or too slow

The game targets 25 FPS (TICK = 0.04s). If your terminal is slow, the game may feel sluggish. Try reducing the terminal font size or using a lighter terminal emulator.

### Save file not working

1. Saves are only supported in CPU mode
2. Check `~/.pong/save.json` exists and is valid JSON
3. The save file is automatically deleted on game completion

### `Error: setup.sh syntax error`

```bash
bash setup.sh
```

Run with bash, not sh. Some systems have dash as /bin/sh which doesn't support all bash syntax.

## File Integrity

If the game behaves strangely, verify the file hasn't been corrupted:

```bash
python3 pong.py --verify
# or
sha256sum -c SHA256SUMS
```

## Getting Help

If none of these solutions work, [open an issue](https://github.com/antoniosdimidgamedev/pong/issues) with:
- Your OS and version
- Terminal emulator
- Python version (`python3 --version`)
- Full error message (or screenshot)
