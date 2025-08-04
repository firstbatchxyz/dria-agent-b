import os
import pathlib
import json
import sys
from typing import List

# Add project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.schemas import StaticMemory
from training import MEMORY_PATH

def load_static_memory_from_example_data(memory_dir: pathlib.Path) -> StaticMemory:
    """
    Load a static memory from a memory directory in example_data format.
    """
    base_memory_path = memory_dir / "base_memory.json"
    
    if not base_memory_path.exists():
        raise FileNotFoundError(f"base_memory.json not found in {memory_dir}")
    
    try:
        with open(base_memory_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convert mem_id to memory_id to match StaticMemory schema
            if "mem_id" in data:
                data["memory_id"] = data.pop("mem_id")
            
            # Compatibility layer for Pydantic v1 vs v2
            if hasattr(StaticMemory, 'model_validate'):
                # Pydantic v2
                return StaticMemory.model_validate(data)
            else:
                # Pydantic v1
                return StaticMemory.parse_obj(data)
            
    except Exception as e:
        raise ValueError(f"Error loading static memory from {base_memory_path}: {e}")

def load_all_static_memories(data_dir: str = "instances") -> List[StaticMemory]:
    """
    Load all static memories from data directory (instances/ or example_data/ structure).
    """
    input_path = pathlib.Path(data_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Find all memory directories
    memory_dirs = []
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
        raise ValueError(f"No memory directories found in {data_dir}")
    
    # Sort for consistent ordering
    memory_dirs.sort(key=lambda x: x.name)
    
    static_memories = []
    for memory_dir in memory_dirs:
        print(f"Loading static memory from {memory_dir.name}...")
        static_memory = load_static_memory_from_example_data(memory_dir)
        static_memories.append(static_memory)
    
    return static_memories

def load_static_memory(path: str) -> StaticMemory:
    """
    Load a single static memory from the old format (for backward compatibility).
    """
    try:
        with open(path, "r") as f:
            # Compatibility layer for Pydantic v1 vs v2
            if hasattr(StaticMemory, 'model_validate_json'):
                # Pydantic v2
                return StaticMemory.model_validate_json(f.read())
            else:
                # Pydantic v1
                return StaticMemory.parse_raw(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(f"Static memory file not found at {path}")

def instantiate_memory(memory_base_path: str = MEMORY_PATH, data_dir: str = "instances"):
    """
    Instantiate all memory directories from data directory (instances/ or example_data/).
    """
    try:
        # Load all static memories from data directory
        static_memories = load_all_static_memories(data_dir)
        
        print(f"Found {len(static_memories)} static memories to instantiate")
        
        # Create base memory directory if it doesn't exist
        if not os.path.exists(memory_base_path):
            os.makedirs(memory_base_path, exist_ok=True)
            print(f"Created base memory directory: {memory_base_path}")
        
        # Instantiate each memory
        for static_memory in static_memories:
            memory_path = os.path.join(memory_base_path, static_memory.memory_id)
            
            # Remove existing memory if it exists, then create fresh
            if os.path.exists(memory_path):
                print(f"Resetting existing memory: {static_memory.memory_id}")
                static_memory.reset(memory_base_path)
            else:
                print(f"Creating new memory: {static_memory.memory_id}")
                static_memory.instantiate(memory_base_path)
        
        print(f"\n✓ Successfully instantiated {len(static_memories)} memories in {memory_base_path}")
        
    except Exception as e:
        print(f"Error instantiating memories: {e}")
        raise

def reset_all_memories(memory_base_path: str = MEMORY_PATH, data_dir: str = "instances"):
    """
    Reset all memory directories from data directory (instances/ or example_data/).
    """
    try:
        # Load all static memories from data directory
        static_memories = load_all_static_memories(data_dir)
        
        print(f"Resetting {len(static_memories)} memories...")
        
        # Reset each memory
        for static_memory in static_memories:
            print(f"Resetting memory: {static_memory.memory_id}")
            static_memory.reset(memory_base_path)
        
        print(f"\n✓ Successfully reset {len(static_memories)} memories")
        
    except Exception as e:
        print(f"Error resetting memories: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup memory from data directory")
    parser.add_argument("--data_dir", default="data/instances", 
                       help="Directory containing memory_* subdirectories (instances/ or example_data/ structure)")
    parser.add_argument("--memory_path", default=MEMORY_PATH,
                       help="Base path where memories will be instantiated")
    parser.add_argument("--reset", action="store_true",
                       help="Reset existing memories before creating new ones")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_all_memories(args.memory_path, args.data_dir)
    else:
        instantiate_memory(args.memory_path, args.data_dir)