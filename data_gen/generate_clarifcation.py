import os
import argparse
import json
import random
import sys
import asyncio
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from pydantic import BaseModel

# Ensure project root is importable when running under different working dirs
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.utils import TaskType, construct_label  

# Reuse the structured OpenAI calling from generate_filters
try:
    from data_gen.generate_filters import get_model_response_async
except Exception:  # Fallback absolute import name if run differently
    from generate_filters import get_model_response_async


# Optional tqdm progress bars
try:
    from tqdm import tqdm
except Exception:
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else []


class ClarificationKind(Enum):
    """Enumeration of clarification scenarios to synthesize.

    - non_existing_entity: Question references an entity not present in memory
    - non_existing_attribute: Question asks for an attribute missing for an existing entity
    - contradiction: Question contains a detail that contradicts the memory
    """

    NON_EXISTENT_ENTITY = "non_existing_entity"
    NON_EXISTENT_ATTRIBUTE = "non_existing_attribute"
    CONTRADICTION = "contradiction"


class ClarificationSample(BaseModel):
    """Structured sample returned by the LLM."""

    question: str
    answer: str
    rationale: Optional[str] = None


DATAGEN_DIR = Path(__file__).parent.absolute()
CLARIFICATION_PROMPT_PATH = os.path.join(DATAGEN_DIR, "prompts", "clarification.md")

# Local type alias for readability
JSONRecord = Dict[str, object]


def load_clarification_prompt(memory_md: str, kind: ClarificationKind) -> Optional[str]:
    """Load and fill the clarification prompt template from file.

    The template must contain placeholders:
      - {memory}: replaced with the (possibly truncated) memory markdown
      - {scenario}: replaced with the selected clarification scenario value
    """
    try:
        with open(CLARIFICATION_PROMPT_PATH, "r", encoding="utf-8") as f:
            template_str = f.read()
        # Simple placeholder replacement to avoid .format collisions
        return (
            template_str
            .replace("{memory}", memory_md)
            .replace("{scenario}", kind.value)
        )
    except Exception as e:
        print(f"Error loading clarification prompt: {e}")
        return None


def _read_text(path: Path) -> str:
    """Best-effort file read returning empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_system_prompt(path: Path) -> str:
    content = _read_text(path).strip()
    if not content:
        raise FileNotFoundError(f"System prompt file not found or empty: {path}")
    return content


def _iter_memory_dirs(instances_root: Path) -> List[Path]:
    """Find all `memory_*/` directories under the instances (UUID) structure."""
    mem_dirs: List[Path] = []
    for instance_dir in instances_root.iterdir():
        if not instance_dir.is_dir():
            continue
        for sub in instance_dir.iterdir():
            if sub.is_dir() and sub.name.startswith("memory_"):
                mem_dirs.append(sub)
    mem_dirs.sort(key=lambda p: p.name)
    return mem_dirs


def _load_memory_markdown(mem_dir: Path, truncate_chars: int) -> Tuple[str, str]:
    """Load memory markdown content and return (combined_markdown, mem_id)."""
    base_path = mem_dir / "base_memory.json"
    if not base_path.exists():
        raise FileNotFoundError(f"base_memory.json not found in {mem_dir}")
    data = json.loads(_read_text(base_path) or "{}")
    mem_id = data.get("mem_id") or data.get("memory_id")
    user_md = data.get("user_md") or ""
    entities: List[Dict[str, str]] = data.get("entities") or []

    parts: List[str] = []
    if user_md:
        parts.append("# USER\n" + user_md.strip())
    if entities:
        parts.append("# ENTITIES")
        for ent in entities:
            efc = ent.get("entity_file_content") or ""
            if efc:
                parts.append(efc.strip())
    combined = ("\n\n".join(parts)).strip()
    if truncate_chars and len(combined) > truncate_chars:
        combined = combined[:truncate_chars] + "\n\n..."
    if not mem_id:
        raise ValueError(f"No mem_id in {base_path}")
    return combined, mem_id


def _build_prompt(memory_md: str, kind: ClarificationKind) -> str:
    filled = load_clarification_prompt(memory_md, kind)
    if not filled:
        # Fallback minimal prompt if template missing
        return (
            f"Memory snippet:\n{memory_md}\n\n"
            f"Generate ONE clarification sample for scenario='{kind.value}' as JSON: "
            "{ 'question': str, 'answer': str }"
        )
    return filled


async def _generate_for_memory(
    mem_dir: Path,
    sys_prompt: str,
    kinds: List[ClarificationKind],
    model: str,
    truncate_chars: int,
) -> List[JSONRecord]:
    """Generate clarification records for a single memory directory."""
    records: List[JSONRecord] = []
    try:
        memory_md, mem_id = _load_memory_markdown(mem_dir, truncate_chars)
    except Exception as e:
        print(f"Warning: Skipping {mem_dir.name}: {e}")
        return records

    for kind in kinds:
        prompt = _build_prompt(memory_md, kind)
        parsed = await get_model_response_async(ClarificationSample, prompt, model)
        if parsed is None:
            print(f"Warning: Skipping kind={kind.value} for {mem_dir.name}: model failed")
            continue
        user_q = (parsed.question or "").strip()
        ans = (parsed.answer or "").strip()
        if not user_q or not ans:
            continue

        record = {
            "context_messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_q},
            ],
            "label": construct_label(TaskType.CLARIFICATION, ans, mem_id),
        }
        records.append(record)
    return records


async def generate_clarification_dataset(
    instances_root: Path,
    sys_prompt_path: Path,
    model: str,
    seed: Optional[int],
    per_type: int,
    kinds: List[ClarificationKind],
    concurrency: int,
    limit_memories: Optional[int],
    truncate_chars: int,
) -> List[JSONRecord]:
    """Generate clarification dataset across instance memories.

    Returns a flat list of JSON records ready to be written as JSONL.
    """
    rng = random.Random(seed)
    sys_prompt = _load_system_prompt(sys_prompt_path)
    mem_dirs = _iter_memory_dirs(instances_root)
    if not mem_dirs:
        print(f"Warning: No memory directories found under {instances_root}")
        return []

    # Sample memories if requested
    if limit_memories is not None and limit_memories > 0:
        mem_dirs = rng.sample(mem_dirs, k=min(limit_memories, len(mem_dirs)))

    # Expand kinds per memory according to per_type
    per_mem_kinds: Dict[Path, List[ClarificationKind]] = {}
    for md in mem_dirs:
        expanded: List[ClarificationKind] = []
        for k in kinds:
            expanded.extend([k] * max(1, per_type))
        # Randomize order to diversify API calls
        rng.shuffle(expanded)
        per_mem_kinds[md] = expanded

    sem = asyncio.Semaphore(max(1, concurrency))
    results: List[JSONRecord] = []

    async def worker(md: Path) -> List[JSONRecord]:
        async with sem:
            return await _generate_for_memory(
                mem_dir=md,
                sys_prompt=sys_prompt,
                kinds=per_mem_kinds[md],
                model=model,
                truncate_chars=truncate_chars,
            )

    tasks = [worker(md) for md in mem_dirs]
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating clarifications"):
        recs = await coro
        results.extend(recs)
    return results


def _split_train_valid(
    records: List[JSONRecord], train_ratio: float, seed: Optional[int]
) -> Tuple[List[JSONRecord], List[JSONRecord]]:
    """Split records into train and valid sets with a fixed ratio."""
    if not records:
        return [], []
    rng = random.Random(seed)
    rng.shuffle(records)
    n_train = max(1, int(len(records) * train_ratio))
    if n_train >= len(records):
        n_train = len(records) - 1
    return records[:n_train], records[n_train:]


def _write_jsonl(path: Path, rows: List[JSONRecord]) -> None:
    """Write a list of dict rows to JSONL at the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> List[JSONRecord]:
    """Read JSONL file into a list of dicts; returns empty list if missing."""
    if not path.exists():
        return []
    rows: List[JSONRecord] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # Skip malformed lines quietly to avoid stopping the pipeline
                continue
    return rows


def main() -> None:
    """CLI entrypoint to generate clarification samples."""
    p = argparse.ArgumentParser(description="Generate clarification training samples from instances memories")
    p.add_argument("--instances-dir", default=str(PROJECT_ROOT / "data/instances"))
    p.add_argument("--system-prompt", default=str(PROJECT_ROOT / "agent/system_prompt.txt"))
    p.add_argument("--output-dir", default=str(PROJECT_ROOT / "data/openrlhf/one-category/clarification"))
    p.add_argument("--model", default=os.getenv("CLAR_MODEL", os.getenv("FILTER_MODEL", "o3-2025-04-16")))
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--per-type", type=int, default=1, help="Samples per clarification kind per memory")
    p.add_argument("--concurrency", type=int, default=int(os.getenv("CLAR_CONCURRENCY", "64")))
    p.add_argument("--limit-memories", type=int, default=None)
    p.add_argument("--train-ratio", type=float, default=0.97)
    p.add_argument("--truncate-chars", type=int, default=6000, help="Truncate memory text to this many chars")
    p.add_argument("--mix-in-data", action="store_true", help="Uniformly and randomly mix generated clarification samples into data/openrlhf/mixed/{train,valid}.jsonl")
    p.add_argument(
        "--kinds",
        nargs="*",
        default=[k.value for k in ClarificationKind],
        choices=[k.value for k in ClarificationKind],
        help="Which clarification kinds to generate",
    )
    args = p.parse_args()

    instances_root = Path(args.instances_dir)
    sys_prompt_path = Path(args.system_prompt)
    output_dir = Path(args.output_dir)

    if not instances_root.exists():
        raise FileNotFoundError(f"Instances dir not found: {instances_root}")

    kinds = [ClarificationKind(k) for k in args.kinds]

    async def runner():
        recs = await generate_clarification_dataset(
            instances_root=instances_root,
            sys_prompt_path=sys_prompt_path,
            model=args.model,
            seed=args.seed,
            per_type=max(1, int(args.per_type)),
            kinds=kinds,
            concurrency=max(1, int(args.concurrency)),
            limit_memories=args.limit_memories,
            truncate_chars=max(500, int(args.truncate_chars)),
        )

        if not recs:
            print("No records generated.")
            return

        train_rows, valid_rows = _split_train_valid(recs, args.train_ratio, args.seed)
        train_path = output_dir / "train.jsonl"
        valid_path = output_dir / "valid.jsonl"

        if args.mix_in_data:
            # Read existing mixed dataset and append, then reshuffle uniformly
            mixed_dir = PROJECT_ROOT / "data/openrlhf/mixed"
            mixed_train = _read_jsonl(mixed_dir / "train.jsonl")
            mixed_valid = _read_jsonl(mixed_dir / "valid.jsonl")

            # Mix uniformly: combine and shuffle
            rng = random.Random(args.seed)
            mixed_train.extend(train_rows)
            mixed_valid.extend(valid_rows)
            rng.shuffle(mixed_train)
            rng.shuffle(mixed_valid)

            # Write back into mixed dataset
            _write_jsonl(mixed_dir / "train.jsonl", mixed_train)
            _write_jsonl(mixed_dir / "valid.jsonl", mixed_valid)

            # Also save a copy under clarification output for traceability
            _write_jsonl(train_path, train_rows)
            _write_jsonl(valid_path, valid_rows)

            print(f"\n✓ mixed {len(train_rows)} train and {len(valid_rows)} valid clarification records into data/openrlhf/mixed")
            print(f"✓ mixed sizes: train={len(mixed_train)}, valid={len(mixed_valid)}")
        else:
            # Default: write to one-category/clarification directory
            _write_jsonl(train_path, train_rows)
            _write_jsonl(valid_path, valid_rows)

            print(f"\n✓ wrote {train_path} ({len(train_rows)} records)")
            print(f"✓ wrote {valid_path} ({len(valid_rows)} records)")

        # Stats
        print(f"✓ total clarification records: {len(recs)}")
        print("✓ kinds:", ", ".join(args.kinds))

    asyncio.run(runner())


if __name__ == "__main__":
    main()


