#!/usr/bin/env python3
import os, sys, hashlib

_HASH_FILE = os.path.join(os.path.dirname(__file__), "SHA256SUMS")


def _verify():
    if not os.path.isfile(_HASH_FILE):
        print("SHA256SUMS not found — cannot verify.")
        sys.exit(1)

    core = os.path.join(os.path.dirname(__file__), "src", "pong", "core.py")
    if not os.path.isfile(core):
        print("core.py not found.")
        sys.exit(1)

    actual = hashlib.sha256(open(core, "rb").read()).hexdigest()
    with open(_HASH_FILE) as f:
        expected, path = f.read().strip().split(None, 1)

    if actual == expected:
        print(f"OK  {path}")
        return True
    else:
        print(f"FAIL  {path}")
        print(f"  expected: {expected}")
        print(f"  actual:   {actual}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--verify", "-V"):
        _verify()
    else:
        os.environ.setdefault("TERM", "xterm-256color")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from pong.core import main
        main()
