#!/usr/bin/env sh
set -e

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found."
    echo "  Termux:       pkg install python"
    echo "  Debian/Ubuntu: apt install python3"
    echo "  Alpine:        apk add python3"
    echo "  macOS:         brew install python"
    exit 1
fi

DIR=$(dirname "$0")
cd "$DIR"

echo "Using: $($PYTHON --version)"
echo "Checking dependencies..."

$PYTHON -c "
import curses, platform, os, sys
print(f'  OS: {platform.system()} {platform.release()}')
print(f'  Arch: {platform.machine()}')
print(f'  Python: {platform.python_version()}')
try:
    stdscr = curses.initscr()
    curses.endwin()
    print('  curses: OK')
except:
    curses.endwin()
    print('  curses: FAIL — install ncurses')
    print('    Termux: pkg install ncurses')
    sys.exit(1)
"

echo ""
echo "All good. Run:  $PYTHON pong.py"
