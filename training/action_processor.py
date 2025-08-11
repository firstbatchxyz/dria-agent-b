import os
from typing import Callable, Tuple, Dict

from agent.utils import format_results
from agent.engine import execute_sandboxed_code
from training import MEMORY_PATH
from training.utils import Task, MAX_STEPS


def calculate_python_reward(python_code: str, step_num: int) -> float:
    """Calculate reward for python actions in all tasks."""
    # Only give rewards for steps 0-4, no rewards after step 4
    if step_num > 4:
        return 0.0
    
    # Scale down reward based on step number - at MAX_STEPS/2, reward becomes 0
    scaling_factor = max(0.0, 1.0 - (2 * step_num / MAX_STEPS))
    
    reward_addition = 0.05 * scaling_factor
    if step_num == 0:
        # check if inside the python code there is one of the following:
        # 1. check_if_file_exists("user.md") or check_if_file_exists('user.md')
        # 2. read_file("user.md") or read_file('user.md')
        # We need the exact string match for these
        desired_strings = [
            "check_if_file_exists('user.md')",
            "check_if_file_exists(\"user.md\")",
            "read_file('user.md')",
            "read_file(\"user.md\")",
        ]

        desired_strings_found = False
        for string in desired_strings:
            if string in python_code:
                desired_strings_found = True
                break

        if desired_strings_found:
            reward_addition += 0.10 * scaling_factor
    
    return reward_addition


def process_action_base(
    observation: str,
    action: str,
    python_code: str,
    reply: str,
    thoughts: str,
    task: Task,
    thoughts_min_length: int,
    step_num: int,
    reply_reward_calculator: Callable[[str, str, Task, Dict[str, str]], float],
    mem_ids_dumps_dict: Dict[str, str]
) -> Tuple[float, bool, str]:
    """
    Base function to process actions for both retrieval and update tasks.
    
    Args:
        observation: The input prompt/expression
        action: The language model's response
        python_code: Extracted python code from action
        reply: Extracted reply from action
        thoughts: Extracted thoughts from action
        task: The task object containing answer
        thoughts_min_length: Minimum length required for thoughts
        step_num: Current step number
        reply_reward_calculator: Function to calculate reward for reply actions
        mem_ids_dumps_dict: Dictionary of memory IDs and their dumps

    Returns:
        tuple: (reward, done, next_observation)
    """
    # Initialize reward
    reward = 0.0
    
    # Check if the action contains a python code, reply, or thoughts block
    python_code_exists = len(python_code.strip()) > 0
    reply_exists = len(reply.strip()) > 0
    #thoughts_exists = len(thoughts.strip()) > 0
    #thoughts_long_enough = len(thoughts.strip()) > thoughts_min_length

    
    done = False

    if python_code_exists and reply_exists:
        next_observation = (
            observation + action + 
            "\nuser\n" +
            "\n [ERROR] Choose one action: either explore with <python> ... </python> OR provide final answer with <reply> ... </reply>." +
            "\n [HINT] If you haven't found the answer yet, use <python> to interact with the memory. If you're confident, use <reply>." +
            "\nassistant\n"
        )
    elif python_code_exists:
        local_vars, error_msg = execute_sandboxed_code(
            code=python_code,
            allowed_path=os.path.join(MEMORY_PATH, task.mem_id),
            import_module="agent.tools",
        )

        next_observation = (
            observation + action +
            "\nuser\n" +
            format_results(local_vars, error_msg) +
            ("\nassistant\n")
        )

        # Use the internal python reward calculator
        reward += calculate_python_reward(python_code, step_num)
        
    elif reply_exists:
        # Use the provided reply reward calculator
        reward += 2.0 * reply_reward_calculator(observation, reply, task, mem_ids_dumps_dict)
        done = True

        next_observation = (
            observation + action + "\n"
        )
    else:
        # Handle the case where the model output didn't contain a recognised
        # block so that `next_observation` is always defined.
        next_observation = (
            observation + action +
            "\nuser\n" +
            "\n [ERROR] Missing action blocks. You must either:" +
            "\n   1. Use <python>...</python> to interact with the memory" +
            "\n   2. Use <reply>...</reply> to provide your final answer to the user" +
            "\nassistant\n"
        )

    # Clamp reward to reasonable bounds - allow negative penalties but cap positive rewards at 1.0
    reward = min(reward, 1.0)
    #reward = max(reward, 0.0)
    
    return reward, done, next_observation 