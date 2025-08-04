from pathlib import Path
import os 

TRAINING_DIR = Path(__file__).parent.absolute()
OBSIDIAN_ROOT = TRAINING_DIR.parent

STATIC_MEMORY_PATH = os.path.join(OBSIDIAN_ROOT, "data", "base_memory.json")
MEMORY_PATH = os.path.join(OBSIDIAN_ROOT, "memory")