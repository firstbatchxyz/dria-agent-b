#!/usr/bin/env python3
"""
Update the system prompt in data/openrlhf/mixed/{train,valid}.jsonl to
the latest version from agent/system_prompt.txt.

Usage:
  python training/scripts/update_system_prompt_in_dataset.py \
    --dataset-dir data/openrlhf/mixed \
    --prompt-file agent/system_prompt.txt
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed reading {path}: {e}")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # Skip malformed lines
                continue
    return rows


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def update_records_with_prompt(rows: List[Dict[str, Any]], system_prompt: str) -> int:
    """Replace/insert the system prompt in context_messages.

    Returns the number of records updated.
    """
    updated = 0
    for rec in rows:
        cms = rec.get("context_messages")
        if not isinstance(cms, list) or not cms:
            continue
        # Find first system message
        sys_msg = None
        for msg in cms:
            if isinstance(msg, dict) and msg.get("role") == "system":
                sys_msg = msg
                break
        if sys_msg is None:
            # Prepend a system message if missing
            cms.insert(0, {"role": "system", "content": system_prompt})
            updated += 1
        else:
            if sys_msg.get("content") != system_prompt:
                sys_msg["content"] = system_prompt
                updated += 1
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync mixed dataset with latest system prompt")
    ap.add_argument("--dataset-dir", default="data/openrlhf/mixed")
    ap.add_argument("--prompt-file", default="agent/system_prompt.txt")
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir)
    prompt_path = Path(args.prompt_file)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset dir not found: {dataset_dir}")
    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {prompt_path}")

    system_prompt = read_text(prompt_path).strip()
    if not system_prompt:
        raise RuntimeError("Provided system prompt is empty")

    for name in ("train.jsonl", "valid.jsonl"):
        path = dataset_dir / name
        if not path.exists():
            print(f"Skip missing: {path}")
            continue
        rows = read_jsonl(path)
        updated = update_records_with_prompt(rows, system_prompt)
        if updated:
            write_jsonl(path, rows)
            print(f"✓ Updated {updated} records in {path}")
        else:
            print(f"No changes needed in {path}")


if __name__ == "__main__":
    main()


