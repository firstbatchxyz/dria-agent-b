from typing import Dict

from training.reward import get_clarification_reward
from training.utils import Task, extract_question


def calculate_clarification_reply_reward(observation: str, reply: str, task: Task, mem_ids_dumps_dict: Dict[str, str]) -> float:
    """Calculate reward for reply actions in clarification tasks.

    Uses only the user question and the agent's reply, as clarification is judged
    by adherence to clarification behavior (no fabrication, helpful follow-up).
    """
    question = extract_question(observation)
    return get_clarification_reward(question=question, agent_reply=reply, debug=True)


