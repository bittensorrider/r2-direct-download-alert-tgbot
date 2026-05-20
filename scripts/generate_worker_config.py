#!/usr/bin/env python3
"""Generate R2 bucket bindings for worker/wrangler.toml from R2_BUCKETS in .env."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
WRANGLER_FILE = ROOT / "worker" / "wrangler.toml"
MARKER_START = "# --- AUTO-GENERATED BUCKETS (scripts/generate_worker_config.py) ---"
MARKER_END = "# --- END AUTO-GENERATED BUCKETS ---"


def binding_name(bucket: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]", "_", bucket).upper().strip("_")
    if not slug:
        raise ValueError(f"Invalid bucket name: {bucket!r}")
    if slug[0].isdigit():
        slug = f"B_{slug}"
    return f"BUCKET_{slug}"


def load_buckets() -> list[str]:
    if not ENV_FILE.exists():
        print(f"Missing {ENV_FILE}. Copy .env.example to .env first.", file=sys.stderr)
        sys.exit(1)

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("R2_BUCKETS="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            buckets = [part.strip() for part in value.split(",") if part.strip()]
            if buckets:
                return buckets

    print("Set R2_BUCKETS=bucket-a,bucket-b in .env", file=sys.stderr)
    sys.exit(1)


def render_bucket_section(buckets: list[str]) -> tuple[str, str]:
    blocks: list[str] = []
    routes: dict[str, str] = {}

    for bucket in buckets:
        binding = binding_name(bucket)
        blocks.append(
            "\n".join(
                [
                    "[[r2_buckets]]",
                    f'binding = "{binding}"',
                    f'bucket_name = "{bucket}"',
                ]
            )
        )
        routes[bucket] = binding

    return "\n\n".join(blocks), json.dumps(routes, separators=(",", ":"))


def upsert_var(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}\s*=\s*.*$", re.MULTILINE)
    line = f'{key} = \'{value}\'' if key == "BUCKET_ROUTES" else f"{key} = {value}"
    if pattern.search(text):
        return pattern.sub(line, text, count=1)

    if "[vars]" in text:
        return text.replace("[vars]", f"[vars]\n{line}", 1)

    return text.rstrip() + f"\n\n[vars]\n{line}\n"


def patch_wrangler(section: str, routes_json: str) -> None:
    text = WRANGLER_FILE.read_text(encoding="utf-8") if WRANGLER_FILE.exists() else ""
    generated_block = f"{MARKER_START}\n{section}\n{MARKER_END}"

    if MARKER_START in text and MARKER_END in text:
        before = text.split(MARKER_START)[0].rstrip()
        after = text.split(MARKER_END, 1)[1]
        text = f"{before}\n\n{generated_block}{after}"
    else:
        text = text.rstrip() + "\n\n" + generated_block + "\n"

    text = upsert_var(text, "BUCKET_ROUTES", routes_json)
    WRANGLER_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    buckets = load_buckets()
    section, routes_json = render_bucket_section(buckets)
    patch_wrangler(section, routes_json)
    print(f"Updated {WRANGLER_FILE} for {len(buckets)} bucket(s):")
    for bucket in buckets:
        print(f"  - {bucket}")


if __name__ == "__main__":
    main()
