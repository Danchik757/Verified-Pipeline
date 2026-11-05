"""Small local contract checks; scientific execution is not implemented yet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .identity import sha256_file, stage_run_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verified-pipeline")
    commands = parser.add_subparsers(dest="command", required=True)
    fingerprint = commands.add_parser("fingerprint", help="validate and fingerprint a resolved stage specification")
    fingerprint.add_argument("spec", type=Path)
    check = commands.add_parser("check-source", help="verify one candidate source file against a recorded SHA-256")
    check.add_argument("path", type=Path)
    check.add_argument("expected_sha256")
    args = parser.parse_args(argv)
    try:
        if args.command == "fingerprint":
            spec = json.loads(args.spec.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON constant {value}")))
            print(json.dumps({"schema_version": 1, "run_id": stage_run_id(spec)}, sort_keys=True))
        else:
            actual = sha256_file(args.path)
            if actual != args.expected_sha256:
                raise ValueError(f"source hash mismatch: expected {args.expected_sha256}, got {actual}")
            print(json.dumps({"sha256": actual, "verified": True}, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
