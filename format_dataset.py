#!/usr/bin/env python3
"""
format_dataset.py
Convert example_data/ multi-memory structure -> data/openrlhf/train.jsonl and valid.jsonl
"""

import argparse, json, pathlib
from typing import List, Dict, Any

from training.utils import TaskType, construct_label

def load_memory_data(memory_dir: pathlib.Path) -> Dict[str, Any]:
    """Load all data for a single memory directory."""
    base_memory_path = memory_dir / "base_memory.json"
    retrieval_path = memory_dir / "retrieval_questions.json"
    update_path = memory_dir / "update_queries.json"
    
    # Check if all required files exist
    if not base_memory_path.exists():
        raise FileNotFoundError(f"base_memory.json not found in {memory_dir}")
    if not retrieval_path.exists():
        raise FileNotFoundError(f"retrieval_questions.json not found in {memory_dir}")
    if not update_path.exists():
        raise FileNotFoundError(f"update_queries.json not found in {memory_dir}")
    
    # Load base memory
    base_memory = json.loads(base_memory_path.read_text(encoding="utf-8"))
    memory_id = base_memory["mem_id"]
    
    # Load retrieval questions
    retrieval_data = json.loads(retrieval_path.read_text(encoding="utf-8"))
    
    # Load update queries
    update_data = json.loads(update_path.read_text(encoding="utf-8"))
    
    return {
        "memory_id": memory_id,
        "base_memory": base_memory,
        "retrieval": retrieval_data,
        "update": update_data
    }

def process_retrieval_questions(memory_data: Dict[str, Any], sys_prompt: str) -> List[Dict[str, Any]]:
    """Process retrieval questions for a memory in hop order (0, 1, 2)."""
    records = []
    memory_id = memory_data["memory_id"]
    retrieval_data = memory_data["retrieval"]
    
    # Process in order: 0_hop, 1_hop, 2_hop
    for hop_level in ["0_hop", "1_hop", "2_hop"]:
        if hop_level in retrieval_data:
            hop_data = retrieval_data[hop_level]
            
            # Handle both array format and single object format
            if isinstance(hop_data, list):
                # Array format (like 0_hop typically)
                items = hop_data
            else:
                # Single object format (some 1_hop, 2_hop cases)
                items = [hop_data]
            
            for i, item in enumerate(items):
                try:
                    # Handle both single questions and lists of questions
                    questions = item["q"]
                    if isinstance(questions, (list, tuple)):
                        iterator = questions
                    else:
                        iterator = [questions]
                    
                    for q in iterator:
                        record = {
                            "context_messages": [
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": q}
                            ],
                            "label": construct_label(TaskType.RETRIEVAL, item["a"], memory_id)
                        }
                        records.append(record)
                except Exception as e:
                    print(f"Error processing {hop_level} item {i} in memory {memory_id}: {e}")
                    print(f"Item type: {type(item)}, Item content: {item}")
                    print(f"Hop data type: {type(hop_data)}, Hop data: {hop_data}")
                    raise
    
    return records

def process_update_queries(memory_data: Dict[str, Any], sys_prompt: str) -> List[Dict[str, Any]]:
    """Process update queries for a memory in hop order (0, 1, 2)."""
    records = []
    memory_id = memory_data["memory_id"]
    update_data = memory_data["update"]
    
    # Process in order: 0_hop, 1_hop, 2_hop
    for hop_level in ["0_hop", "1_hop", "2_hop"]:
        if hop_level in update_data:
            hop_data = update_data[hop_level]
            
            # Handle both array format and single object format
            if isinstance(hop_data, list):
                # Array format (like 0_hop typically)
                items = hop_data
            else:
                # Single object format (some 1_hop, 2_hop cases)
                items = [hop_data]
            
            for item in items:
                record = {
                    "context_messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": item["query"]}
                    ],
                    "label": construct_label(TaskType.UPDATE, item["diff"], memory_id)
                }
                records.append(record)
    
    return records

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input_dir", default="data/instances")
    p.add_argument("--prompt", default="agent/system_prompt.txt")
    p.add_argument("--out_dir", default="data/openrlhf")
    args = p.parse_args()

    # Load system prompt
    sys_prompt = pathlib.Path(args.prompt).read_text(encoding="utf-8").strip()
    
    # Find all memory directories across all instance folders
    input_path = pathlib.Path(args.input_dir)
    memory_dirs = []
    
    if not input_path.exists():
        print(f"Input directory not found: {args.input_dir}")
        return
    
    # Check if this is the instances structure (UUID folders) or direct memory structure
    subdirs = [d for d in input_path.iterdir() if d.is_dir()]
    
    if any(d.name.startswith("memory_") for d in subdirs):
        # Direct memory structure (like example_data)
        memory_dirs = [d for d in subdirs if d.name.startswith("memory_")]
        print(f"Found direct memory structure with {len(memory_dirs)} memory directories")
    else:
        # Instances structure with UUID folders
        instance_count = 0
        for instance_dir in subdirs:
            if instance_dir.is_dir():
                instance_memory_dirs = [d for d in instance_dir.iterdir() if d.is_dir() and d.name.startswith("memory_")]
                memory_dirs.extend(instance_memory_dirs)
                if instance_memory_dirs:
                    instance_count += 1
        
        print(f"Found instances structure with {instance_count} instance folders containing {len(memory_dirs)} total memory directories")
    
    if not memory_dirs:
        print(f"No memory directories found in {args.input_dir}")
        return
    
    # Collect retrieval and update records separately to ensure even distribution
    all_retrieval_records = []
    all_update_records = []
    
    # Sort memory directories by name for consistent ordering
    memory_dirs.sort(key=lambda x: x.name)
    
    skipped_count = 0
    for memory_dir in memory_dirs:
        print(f"Processing {memory_dir.name}...")
        
        try:
            # Load memory data
            memory_data = load_memory_data(memory_dir)
            
            # Process retrieval questions first (0, 1, 2 hop order)
            retrieval_records = process_retrieval_questions(memory_data, sys_prompt)
            all_retrieval_records.extend(retrieval_records)
            
            # Then process update queries (0, 1, 2 hop order)
            update_records = process_update_queries(memory_data, sys_prompt)
            all_update_records.extend(update_records)
            
            print(f"  - Added {len(retrieval_records)} retrieval records")
            print(f"  - Added {len(update_records)} update records")
        except FileNotFoundError as e:
            print(f"  - Skipped: {e}")
            skipped_count += 1
            continue

    # Split each task type separately: 90% train, 10% validation
    retrieval_train_size = int(len(all_retrieval_records) * 0.97)
    update_train_size = int(len(all_update_records) * 0.97)
    
    retrieval_train = all_retrieval_records[:retrieval_train_size]
    retrieval_valid = all_retrieval_records[retrieval_train_size:]
    
    update_train = all_update_records[:update_train_size]
    update_valid = all_update_records[update_train_size:]
    
    # Combine train and validation sets maintaining order: retrieval first, then update
    train_records = retrieval_train + update_train
    valid_records = retrieval_valid + update_valid

    # Create output directory
    pathlib.Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    
    # Write train.jsonl
    train_path = pathlib.Path(args.out_dir) / "train.jsonl"
    with train_path.open("w", encoding="utf-8") as fh:
        for record in train_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Write valid.jsonl
    valid_path = pathlib.Path(args.out_dir) / "valid.jsonl"
    with valid_path.open("w", encoding="utf-8") as fh:
        for record in valid_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    total_records = len(all_retrieval_records) + len(all_update_records)
    
    print(f"\n✓ wrote {train_path} ({len(train_records)} records)")
    print(f"  - Retrieval: {len(retrieval_train)} records")
    print(f"  - Update: {len(update_train)} records")
    print(f"✓ wrote {valid_path} ({len(valid_records)} records)")
    print(f"  - Retrieval: {len(retrieval_valid)} records")
    print(f"  - Update: {len(update_valid)} records")
    print(f"✓ total records processed: {total_records}")
    print(f"✓ memories processed: {len(memory_dirs) - skipped_count}, skipped: {skipped_count}")
    print(f"✓ data ordering: retrieval (0,1,2 hop) then update (0,1,2 hop) for each memory")
    print(f"✓ even distribution maintained in train/validation split")

if __name__ == "__main__":
    main()