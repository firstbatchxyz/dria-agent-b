import os
import argparse
import json
import random
import sys
import asyncio
import re
from pathlib import Path
from enum import Enum
from typing import List, Tuple, Optional

from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

# Ensure project root is importable when running under different working dirs
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.utils import DELIMITER, TaskType, parse_answer_and_optional_filter

# Optional tqdm progress bars
try:
    from tqdm import tqdm
except Exception:
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else []

load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATAGEN_DIR = Path(__file__).parent.absolute()
OBSIDIAN_ROOT = DATAGEN_DIR.parent
QA_FILTER_PROMPT_PATH = os.path.join(DATAGEN_DIR, "prompts", "qa_filter.md")

class ObfuscationType(Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NO = "no"

class QAFilterResponse(BaseModel):
    filters: str
    answer: str


def load_qa_filter_prompt(base_memory: str, question: str) -> Optional[str]:
    try:
        with open(QA_FILTER_PROMPT_PATH, "r", encoding="utf-8") as f:
            template_str = f.read()

        # Get a random obfuscation type
        obfuscation_type = random.choice(list(ObfuscationType))
        
        # Use direct placeholder replacement to avoid issues with JSON braces in template
        template = template_str.replace("{base_memory}", base_memory).replace("{question}", question).replace("{obfuscation_type}", obfuscation_type.value)
        return template
    except Exception as e:
        print(f"Error loading QA filter prompt: {e}")
        return None


def get_model_response(schema: BaseModel, prompt: str, model: str) -> Optional[BaseModel]:
    """
    Get a structured response from the OpenAI model

    Args:
        schema: The schema of the response
        prompt: The prompt to send to the model
        model: The model to use

    Returns:
        The structured response
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    for attempt in range(3):
        try:
            response = client.responses.parse(
                model=model,
                input=[{"role": "user", "content": prompt}],
                text_format=schema,
            )
            return response.output_parsed
        except Exception as e:
            print(f"OpenAI call failed on attempt {attempt + 1}: {e}")
            if attempt == 2:  # Last attempt
                print("All retry attempts failed")
                return None


async def get_model_response_async(schema: BaseModel, prompt: str, model: str) -> Optional[BaseModel]:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    for attempt in range(3):
        try:
            response = await client.responses.parse(
                model=model,
                input=[{"role": "user", "content": prompt}],
                text_format=schema,
            )
            return response.output_parsed
        except Exception as e:
            print(f"OpenAI async call failed on attempt {attempt + 1}: {e}")
            if attempt == 2:
                print("All retry attempts failed (async)")
                return None


def _split_label(label: str) -> Tuple[str, str, str]:
    parts = label.split(DELIMITER)
    if len(parts) != 3:
        raise ValueError("Malformed label: expected exactly three parts")
    return parts[0], parts[1], parts[2]


def _is_retrieval_label(label: str) -> bool:
    try:
        task_type, _, _ = _split_label(label)
        return task_type == TaskType.RETRIEVAL.value
    except Exception:
        return False


def _label_has_filter(label: str) -> bool:
    try:
        _, _, tail = _split_label(label)
        return "<filter>" in tail and "</filter>" in tail and "<answer>" in tail and "</answer>" in tail
    except Exception:
        return False


def _find_memory_dir(mem_id: str, instances_root: Path) -> Optional[Path]:
    for instance_dir in instances_root.iterdir():
        if not instance_dir.is_dir():
            continue
        candidate = instance_dir / mem_id
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _load_user_md(mem_id: str, instances_root: Path) -> Optional[str]:
    mem_dir = _find_memory_dir(mem_id, instances_root)
    if mem_dir is None:
        return None
    base_memory_path = mem_dir / "base_memory.json"
    if not base_memory_path.exists():
        return None
    try:
        data = json.loads(base_memory_path.read_text(encoding="utf-8"))
        return data.get("user_md")
    except Exception:
        return None


def _extract_question(record: dict) -> Optional[str]:
    try:
        messages: List[dict] = record.get("context_messages", [])
        for msg in messages:
            if msg.get("role") == "user":
                return str(msg.get("content", ""))
        return None
    except Exception:
        return None


def _build_label_with_filter(mem_id: str, filters: str, filtered_answer: str) -> str:
    """
    Build the label tail placing <filter>...</filter> and <answer>...</answer>.
    If inputs already include tags, keep them as-is; otherwise wrap appropriately.
    """
    filt = filters.strip()
    ans = filtered_answer.strip()

    if not filt.lower().startswith("<filter>"):
        filt = f"<filter>\n{filt}\n</filter>"
    if not ans.lower().startswith("<answer>"):
        ans = f"<answer>\n{ans}\n</answer>"

    tail = f"{filt}\n{ans}"
    return f"{TaskType.RETRIEVAL.value}{DELIMITER}{mem_id}{DELIMITER}{tail}"


async def augment_file_with_filters_async(
    dataset_file: Path,
    instances_root: Path,
    model: str,
    seed: Optional[int] = None,
    fraction: float = 0.5,
    concurrency: int = 8,
) -> None:
    """
    Add filters to a fraction of retrieval records in-place using async concurrency.
    Only records that are retrieval and do not already contain filter tags are considered.
    """
    rng = random.Random(seed)
    print(f"Processing dataset: {dataset_file}")

    # Load records
    records: List[dict] = []
    with dataset_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception as e:
                print(f"  - Skipping malformed JSONL line: {e}")

    # Identify candidate indices
    candidates: List[int] = []
    for i, rec in enumerate(records):
        label = rec.get("label", "")
        if _is_retrieval_label(label) and not _label_has_filter(label):
            candidates.append(i)

    if not candidates:
        print("  - No eligible retrieval records found (or all already filtered)")
        return

    target_count = max(1, int(len(candidates) * fraction))
    chosen_indices = set(rng.sample(candidates, k=target_count))

    print(
        f"  - Eligible retrieval records: {len(candidates)} | Selecting: {len(chosen_indices)} (~{int(fraction*100)}%)"
    )

    sem = asyncio.Semaphore(max(1, concurrency))

    def _normalize_filter_for_user(filter_text: str) -> str:
        if not isinstance(filter_text, str):
            return ""
        m = re.search(r"<filter>\s*([\s\S]*?)\s*</filter>", filter_text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else filter_text.strip()

    def _ensure_filter_in_user_message(record: dict, filter_text: str) -> None:
        try:
            if not filter_text or not isinstance(filter_text, str):
                return
            messages: List[dict] = record.get("context_messages", [])
            # find first user message
            for m in messages:
                if m.get("role") == "user":
                    content = str(m.get("content", ""))
                    if "<filter>" in content and "</filter>" in content:
                        return
                    normalized = _normalize_filter_for_user(filter_text)
                    new_content = content.rstrip() + f"\n\n<filter>\n{normalized}\n</filter>"
                    m["content"] = new_content
                    return
        except Exception:
            return

    async def process_idx(idx: int) -> Optional[Tuple[int, str, str]]:
        rec = records[idx]
        label = rec.get("label", "")
        try:
            _, mem_id, _ = _split_label(label)
        except Exception as e:
            print(f"  - Skip idx {idx}: bad label format: {e}")
            return None

        question = _extract_question(rec)
        if not question:
            print(f"  - Skip idx {idx}: could not extract question")
            return None

        user_md = _load_user_md(mem_id, instances_root)
        if not user_md:
            print(f"  - Skip idx {idx}: could not load base memory for {mem_id}")
            return None

        prompt = load_qa_filter_prompt(base_memory=user_md, question=question)
        if not prompt:
            print(f"  - Skip idx {idx}: failed to build prompt")
            return None

        async with sem:
            parsed = await get_model_response_async(QAFilterResponse, prompt, model)

        if parsed is None:
            print(f"  - Skip idx {idx}: model did not return a valid response")
            return None

        new_label = _build_label_with_filter(mem_id, parsed.filters, parsed.answer)
        return idx, new_label, parsed.filters

    tasks = [process_idx(i) for i in chosen_indices]
    results: List[Optional[Tuple[int, str, str]]] = []
    # Use as_completed to update progress bar as tasks finish
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=f"Generating filters: {dataset_file.name}"):
        res = await coro
        results.append(res)

    updated = 0
    for res in results:
        if res is None:
            continue
        idx, new_label, filter_text = res
        records[idx]["label"] = new_label
        _ensure_filter_in_user_message(records[idx], filter_text)
        updated += 1

    if updated == 0:
        print("  - No records updated")
        return

    # Write back in-place
    with dataset_file.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"  ✓ Updated {updated} records in {dataset_file}")

    # Ensure any pre-existing filtered labels also have filters in the user message
    fixed_missing = 0
    for rec in records:
        label = rec.get("label", "")
        if not _label_has_filter(label):
            continue
        try:
            _, _, tail = _split_label(label)
            answer_text, filter_text = parse_answer_and_optional_filter(tail)
            # Append only if missing
            messages: List[dict] = rec.get("context_messages", [])
            user_msg = next((m for m in messages if m.get("role") == "user"), None)
            if user_msg is None:
                continue
            content = str(user_msg.get("content", ""))
            if "<filter>" in content and "</filter>" in content:
                continue
            if filter_text:
                _ensure_filter_in_user_message(rec, filter_text)
                fixed_missing += 1
        except Exception:
            continue
    if fixed_missing:
        # write once more if we fixed any
        with dataset_file.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"  ✓ Ensured filters appear in user messages for {fixed_missing} pre-filtered records")


def main():
    p = argparse.ArgumentParser(description="Augment retrieval dataset with filters for a random half of records")
    p.add_argument("--dataset-dir", default=str(OBSIDIAN_ROOT / "data/openrlhf/mixed"))
    p.add_argument("--train-file", default="train.jsonl")
    p.add_argument("--valid-file", default="valid.jsonl")
    p.add_argument("--instances-dir", default=str(OBSIDIAN_ROOT / "data/instances"))
    p.add_argument("--model", default=os.getenv("FILTER_MODEL", "o3-2025-04-16"))
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--fraction", type=float, default=0.5)
    p.add_argument("--concurrency", type=int, default=int(os.getenv("FILTER_CONCURRENCY", "128")))
    args = p.parse_args()

    dataset_dir = Path(args.dataset_dir)
    instances_root = Path(args.instances_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset dir not found: {dataset_dir}")
    if not instances_root.exists():
        raise FileNotFoundError(f"Instances dir not found: {instances_root}")

    train_path = dataset_dir / args.train_file
    valid_path = dataset_dir / args.valid_file

    if not train_path.exists() or not valid_path.exists():
        raise FileNotFoundError("train.jsonl or valid.jsonl not found in dataset dir")

    async def runner():
        await augment_file_with_filters_async(
            dataset_file=train_path,
            instances_root=instances_root,
            model=args.model,
            seed=args.seed,
            fraction=args.fraction,
            concurrency=args.concurrency,
        )

        await augment_file_with_filters_async(
            dataset_file=valid_path,
            instances_root=instances_root,
            model=args.model,            seed=None if args.seed is None else args.seed + 1,
            fraction=args.fraction,
            concurrency=args.concurrency,
        )

    asyncio.run(runner())


if __name__ == "__main__":
    main()