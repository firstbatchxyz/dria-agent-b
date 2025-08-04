from training.reward import get_retrieval_reward
from training.utils import Task, extract_question

def calculate_retrieval_reply_reward(observation: str, reply: str, task: Task) -> float:
    """Calculate reward for reply actions in retrieval tasks."""
    question = extract_question(observation)
    return get_retrieval_reward(question, reply, task.answer)