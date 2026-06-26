#!/usr/bin/env python3
import os, sys

os.environ.setdefault("TERM", "xterm-256color")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pong.core import main

main()
