#!/usr/bin/env python3
import os, sys, hashlib

_HASH_FILE = os.path.join(os.path.dirname(__file__), "SHA256SUMS")


def _verify():
    if not os.path.isfile(_HASH_FILE):
        print("Error: SHA256SUMS not found. File may be corrupted.", file=sys.stderr)
        sys.exit(1)

    core = os.path.join(os.path.dirname(__file__), "src", "pong", "core.py")
    if not os.path.isfile(core):
        print("Error: core.py not found.", file=sys.stderr)
        sys.exit(1)

    actual = hashlib.sha256(open(core, "rb").read()).hexdigest()
    with open(_HASH_FILE) as f:
        expected, path = f.read().strip().split(None, 1)

    if actual != expected:
        print(
            f"Integrity check FAILED for {path}.\n"
            f"  Expected: {expected}\n"
            f"  Actual:   {actual}\n"
            "The file has been modified or corrupted. Refusing to run.\n"
            "Re-download from: https://github.com/antoniosdimidgamedev/pong",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    _verify()
    os.environ.setdefault("TERM", "xterm-256color")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
    from pong.core import main
    main()
