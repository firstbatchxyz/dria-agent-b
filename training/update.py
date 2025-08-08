import os
from typing import Dict
from training import MEMORY_PATH

from training.utils import Task, extract_python_blocks, dump_folder
from training.reward import get_update_reward

def calculate_update_reply_reward(observation: str, reply: str, task: Task, mem_ids_dumps_dict: Dict[str, str]) -> float:
    """Calculate reward for reply actions in update tasks."""
    # Get the memory path
    memory_path = os.path.join(MEMORY_PATH, task.mem_id)

    # Get the initial folder dump
    initial_folder_dump = mem_ids_dumps_dict[task.mem_id]

    # Get the final folder dump
    final_folder_dump = dump_folder(memory_path)

    reward = get_update_reward(
        user_query=task.answer,
        initial_folder_dump=initial_folder_dump,
        final_folder_dump=final_folder_dump,
        debug=True
    )
    return reward