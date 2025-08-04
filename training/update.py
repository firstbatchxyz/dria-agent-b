from training.utils import Task, extract_python_blocks
from training.reward import get_update_reward

def calculate_update_reply_reward(observation: str, reply: str, task: Task) -> float:
    """Calculate reward for reply actions in update tasks."""
    python_blocks = extract_python_blocks(observation)
    diff = task.answer
    reward = get_update_reward(
        python_blocks=python_blocks,
        diff=diff,
        debug=True
    )
    return reward