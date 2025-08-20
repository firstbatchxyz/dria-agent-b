from typing import Dict

from training.reward import get_retrieval_reward
from training.utils import Task, extract_question, parse_answer_and_optional_filter

def calculate_retrieval_reply_reward(observation: str, reply: str, task: Task, mem_ids_dumps_dict: Dict[str, str]) -> float:
    """Calculate reward for reply actions in retrieval tasks.

    If the label tail includes <filter> and <answer> blocks, pass the filter to the judge prompt logic
    and use the filtered answer as the ground truth.
    """
    question = extract_question(observation)
    gt_answer, filter_text = parse_answer_and_optional_filter(task.answer)
    return get_retrieval_reward(question, reply, gt_answer, filter_text)