#!/usr/bin/env python3
"""
format_dataset.py
Convert example_data/ multi-memory structure -> data/openrlhf/train.jsonl and valid.jsonl
"""

import argparse, json, pathlib, random
from typing import List, Dict, Any, Tuple

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

def process_retrieval_questions(memory_data: Dict[str, Any], sys_prompt: str) -> Dict[str, List[Dict[str, Any]]]:
    """Process retrieval questions for a memory, organized by hop level."""
    memory_id = memory_data["memory_id"]
    retrieval_data = memory_data["retrieval"]
    hop_records = {"0_hop": [], "1_hop": [], "2_hop": []}
    
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
                        hop_records[hop_level].append(record)
                except Exception as e:
                    print(f"Error processing {hop_level} item {i} in memory {memory_id}: {e}")
                    print(f"Item type: {type(item)}, Item content: {item}")
                    print(f"Hop data type: {type(hop_data)}, Hop data: {hop_data}")
                    raise
    
    return hop_records

def process_update_queries(memory_data: Dict[str, Any], sys_prompt: str) -> Dict[str, List[Dict[str, Any]]]:
    """Process update queries for a memory, organized by hop level."""
    memory_id = memory_data["memory_id"]
    update_data = memory_data["update"]
    hop_records = {"0_hop": [], "1_hop": [], "2_hop": []}
    
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
                hop_records[hop_level].append(record)
    
    return hop_records

def combine_data_mixed(all_retrieval_hops: Dict[str, List[Dict[str, Any]]], 
                      all_update_hops: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Combine retrieval and update data mixed by hop level (0_hop first, then 1_hop, then 2_hop)."""
    combined_records = []
    
    # Process each hop level in order
    for hop_level in ["0_hop", "1_hop", "2_hop"]:
        # Combine retrieval and update records for this hop level
        hop_records = all_retrieval_hops[hop_level] + all_update_hops[hop_level]
        # Shuffle the combined records for this hop
        random.shuffle(hop_records)
        # Add shuffled records to combined list
        combined_records.extend(hop_records)
    
    return combined_records

def combine_data_ordered(all_retrieval_hops: Dict[str, List[Dict[str, Any]]], 
                        all_update_hops: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Combine retrieval and update data ordered by category (retrieval first, then update)."""
    combined_records = []
    
    # Add all retrieval records (already in hop order)
    for hop_level in ["0_hop", "1_hop", "2_hop"]:
        combined_records.extend(all_retrieval_hops[hop_level])
    
    # Add all update records (already in hop order)
    for hop_level in ["0_hop", "1_hop", "2_hop"]:
        combined_records.extend(all_update_hops[hop_level])
    
    return combined_records

def combine_data_one_category(data_hops: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Combine data from one category only, ordered by hop level."""
    combined_records = []
    
    # Add records in hop order
    for hop_level in ["0_hop", "1_hop", "2_hop"]:
        combined_records.extend(data_hops[hop_level])
    
    return combined_records

def split_data(records: List[Dict[str, Any]], train_ratio: float = 0.97) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split data into train and validation sets."""
    train_size = int(len(records) * train_ratio)
    return records[:train_size], records[train_size:]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input_dir", default="data/instances")
    p.add_argument("--prompt", default="agent/system_prompt.txt")
    p.add_argument("--out_dir", default="data/openrlhf")
    p.add_argument("--mode", default="mixed", choices=["mixed", "ordered", "one-category"],
                   help="Data generation mode: mixed (interleave by hop), ordered (retrieval first), one-category (single type)")
    p.add_argument("--category", default=None, choices=["retrieval", "update"],
                   help="Category to use for one-category mode (required if mode=one-category)")
    args = p.parse_args()

    # Validate arguments
    if args.mode == "one-category" and args.category is None:
        print("Error: --category must be specified when using --mode one-category")
        return

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
    
    # Initialize data structures to collect records by hop level
    all_retrieval_hops = {"0_hop": [], "1_hop": [], "2_hop": []}
    all_update_hops = {"0_hop": [], "1_hop": [], "2_hop": []}
    
    # Sort memory directories by name for consistent ordering
    memory_dirs.sort(key=lambda x: x.name)
    
    skipped_count = 0
    for memory_dir in memory_dirs:
        print(f"Processing {memory_dir.name}...")
        
        try:
            # Load memory data
            memory_data = load_memory_data(memory_dir)
            
            # Process retrieval questions organized by hop level
            if args.mode != "one-category" or args.category == "retrieval":
                retrieval_hops = process_retrieval_questions(memory_data, sys_prompt)
                for hop_level in ["0_hop", "1_hop", "2_hop"]:
                    all_retrieval_hops[hop_level].extend(retrieval_hops[hop_level])
                
                total_retrieval = sum(len(records) for records in retrieval_hops.values())
                print(f"  - Added {total_retrieval} retrieval records")
            
            # Process update queries organized by hop level
            if args.mode != "one-category" or args.category == "update":
                update_hops = process_update_queries(memory_data, sys_prompt)
                for hop_level in ["0_hop", "1_hop", "2_hop"]:
                    all_update_hops[hop_level].extend(update_hops[hop_level])
                
                total_update = sum(len(records) for records in update_hops.values())
                print(f"  - Added {total_update} update records")
            
        except FileNotFoundError as e:
            print(f"  - Skipped: {e}")
            skipped_count += 1
            continue

    # Combine data based on mode
    if args.mode == "mixed":
        all_records = combine_data_mixed(all_retrieval_hops, all_update_hops)
        print(f"Using mixed mode: interleaving retrieval and update by hop level")
    elif args.mode == "ordered":
        all_records = combine_data_ordered(all_retrieval_hops, all_update_hops)
        print(f"Using ordered mode: retrieval first, then update")
    elif args.mode == "one-category":
        if args.category == "retrieval":
            all_records = combine_data_one_category(all_retrieval_hops)
            print(f"Using one-category mode: retrieval only")
        else:  # args.category == "update"
            all_records = combine_data_one_category(all_update_hops)
            print(f"Using one-category mode: update only")

    # Split into train and validation sets
    train_records, valid_records = split_data(all_records)

    # Construct output directory path based on mode
    if args.mode == "one-category":
        output_dir = pathlib.Path(args.out_dir) / "one-category" / args.category
    else:
        output_dir = pathlib.Path(args.out_dir) / args.mode
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write train.jsonl
    train_path = output_dir / "train.jsonl"
    with train_path.open("w", encoding="utf-8") as fh:
        for record in train_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Write valid.jsonl
    valid_path = output_dir / "valid.jsonl"
    with valid_path.open("w", encoding="utf-8") as fh:
        for record in valid_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Calculate statistics
    total_retrieval = sum(len(records) for records in all_retrieval_hops.values())
    total_update = sum(len(records) for records in all_update_hops.values())
    
    print(f"\n✓ wrote {train_path} ({len(train_records)} records)")
    print(f"✓ wrote {valid_path} ({len(valid_records)} records)")
    print(f"✓ total records processed: {len(all_records)}")
    if args.mode != "one-category":
        print(f"  - Retrieval: {total_retrieval} records")
        print(f"  - Update: {total_update} records")
    print(f"✓ memories processed: {len(memory_dirs) - skipped_count}, skipped: {skipped_count}")
    print(f"✓ data ordering: {args.mode} mode" + (f" ({args.category} only)" if args.mode == "one-category" else ""))

if __name__ == "__main__":
    main()