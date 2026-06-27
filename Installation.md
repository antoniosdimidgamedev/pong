# Installation

## Requirements

- **Python 3.6 or newer**
- **curses module** (built-in on Linux/macOS; see Termux section below)
- **curl** (optional — used for the idle rickroll easter egg)
- No other dependencies

## Linux

```bash
# Install Python (usually pre-installed)
sudo apt install python3  # Debian/Ubuntu
sudo dnf install python3  # Fedora
sudo pacman -S python     # Arch

# Verify curses is available
python3 -c "import curses; print('OK')"

# Run
git clone https://github.com/antoniosdimidgamedev/pong.git
cd pong
python3 pong.py
```

## macOS

```bash
# Install Python (if not already installed)
brew install python3

# Verify curses is available
python3 -c "import curses; print('OK')"

# Run
git clone https://github.com/antoniosdimidgamedev/pong.git
cd pong
python3 pong.py
```

## Termux (Android)

Termux requires a few extra steps:

```bash
# Install Python
pkg update && pkg upgrade
pkg install python

# Install curses (separate package in Termux)
pkg install ncurses

# Verify
python3 -c "import curses; print('OK')"

# Run
git clone https://github.com/antoniosdimidgamedev/pong.git
cd pong
python3 pong.py
```

## File Integrity

To verify the game file hasn't been tampered with:

```bash
python3 pong.py --verify
# or
sha256sum -c SHA256SUMS
```
