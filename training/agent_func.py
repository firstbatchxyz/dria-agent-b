import random
from typing import Any, Dict
import json
import os
import pathlib
import threading
import hashlib

import torch
from openrlhf.utils.agent import AgentExecutorBase, AgentInstanceBase
from vllm import SamplingParams

from agent.utils import extract_reply, extract_python_code, extract_thoughts
from agent.schemas import StaticMemory
from training.action_processor import process_action_base
from training.retrieval import calculate_retrieval_reply_reward
from training.update import calculate_update_reply_reward
from training.clarification import calculate_clarification_reply_reward
from training.utils import Task, TaskType, extract_task_from_label, remove_all_thinks_except_last, MAX_STEPS, dump_folder
from training import MEMORY_PATH

# Per-worker lock dictionaries (initialized lazily to avoid Ray serialization issues)
_memory_locks = None
_locks_lock = None

# Load hyperparameters
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        THOUGHTS_MIN_LENGTH = config["hyperparameters"]["thoughts_min_length"]
except:
    raise ValueError("config.json not found or the thoughts_min_length key is not present in hyperparameters")


def get_memory_lock(memory_id: str) -> threading.Lock:
    """
    Get or create a lock for a specific memory ID.
    Thread-safe creation of per-memory locks.
    Initializes per-worker locks lazily to avoid Ray serialization issues.
    
    Args:
        memory_id: The memory ID to get a lock for
        
    Returns:
        threading.Lock: A lock specific to this memory_id
    """
    global _memory_locks, _locks_lock
    
    # Initialize locks lazily per worker to avoid Ray serialization issues
    if _locks_lock is None:
        _locks_lock = threading.Lock()
    if _memory_locks is None:
        _memory_locks = {}
    
    with _locks_lock:
        if memory_id not in _memory_locks:
            _memory_locks[memory_id] = threading.Lock()
        return _memory_locks[memory_id]


def is_memory_fresh(memory_id: str, expected_content_hash: str) -> bool:
    """
    Check if memory is already in the expected fresh state.
    
    Args:
        memory_id: The memory ID to check
        expected_content_hash: Hash of expected user.md content
        
    Returns:
        bool: True if memory is already fresh
    """
    try:
        memory_path = os.path.join(MEMORY_PATH, memory_id)
        user_md_path = os.path.join(memory_path, "user.md")
        
        if not os.path.exists(user_md_path):
            return False
            
        # Read current content and hash it
        with open(user_md_path, "r", encoding="utf-8") as f:
            current_content = f.read()
        
        current_hash = hashlib.md5(current_content.encode()).hexdigest()
        return current_hash == expected_content_hash
        
    except Exception:
        return False


def reset_memory_for_episode(memory_id: str, instances_dir: str = "data/instances") -> bool:
    """
    Thread-safe reset of a specific memory to its original state before training episode.
    Uses per-memory locks to prevent race conditions in async training.
    
    Args:
        memory_id: The memory ID to reset (e.g., 'memory_f707bc1c8e7848cc991394760ca9005b')
        instances_dir: Directory containing the original memory instances
    
    Returns:
        bool: True if reset successful, False otherwise
    """
    # Get the lock for this specific memory_id
    memory_lock = get_memory_lock(memory_id)
    
    with memory_lock:  # Only one agent can reset this memory at a time
        try:
            # Ensure absolute paths to avoid working directory issues
            if not os.path.isabs(instances_dir):
                # Get the project root directory (parent of training directory)
                training_dir = pathlib.Path(__file__).parent.absolute()
                project_root = training_dir.parent
                instances_dir = os.path.join(project_root, instances_dir)
            
            # Find the memory directory in instances
            instances_path = pathlib.Path(instances_dir)
            if not instances_path.exists():
                print(f"Warning: Instances directory not found: {instances_dir}")
                print(f"Current working directory: {os.getcwd()}")
                print(f"Resolved instances path: {instances_path.absolute()}")
                return False
            
            # Search for the memory in all instance folders
            memory_dir = None
            for instance_dir in instances_path.iterdir():
                if instance_dir.is_dir():
                    potential_memory_dir = instance_dir / memory_id
                    if potential_memory_dir.exists():
                        memory_dir = potential_memory_dir
                        break
            
            if not memory_dir:
                print(f"Warning: Memory {memory_id} not found in instances")
                return False
            
            # Load the base memory
            base_memory_path = memory_dir / "base_memory.json"
            if not base_memory_path.exists():
                print(f"Warning: base_memory.json not found in {memory_dir}")
                return False
            
            # Load and validate the static memory
            with open(base_memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert mem_id to memory_id to match StaticMemory schema
                if "mem_id" in data:
                    data["memory_id"] = data.pop("mem_id")
                static_memory = StaticMemory.model_validate(data)
            
            # Calculate expected content hash
            expected_content_hash = hashlib.md5(static_memory.user_md.encode()).hexdigest()
            
            # Check if memory is already fresh (optimization to avoid unnecessary resets)
            if is_memory_fresh(memory_id, expected_content_hash):
                return True
            
            # Reset the memory: manually remove existing files and recreate
            memory_full_path = os.path.join(MEMORY_PATH, memory_id)
            
            # Remove existing memory directory if it exists
            if os.path.exists(memory_full_path):
                import shutil
                shutil.rmtree(memory_full_path)
            
            # Use instantiate to create fresh memory (this adds memory_id to path correctly)
            static_memory.instantiate(MEMORY_PATH)
            
            return True
            
        except Exception as e:
            print(f"Error resetting memory {memory_id}: {e}")
            return False


class AgentInstance(AgentInstanceBase):
    async def __init__(self, *args, **kwargs):
        self.step_idx = 0
        self.max_steps = MAX_STEPS
        self.mem_ids_dumps_dict = {}

    async def reset(self, states: dict, **kwargs):
        """Initialize the environment and return initial observation

        Args:
            states: Dictionary containing observation and label

        Returns:
            dict: Initial state with observation
        """
        # Reset step counter for new episode
        self.step_idx = 0
        
        # Extract memory ID from label and reset memory state
        label = states.get("label", "")
        if label:
            try:
                # Extract task to get memory ID
                task = extract_task_from_label(label)
                memory_id = task.mem_id
                
                if memory_id:
                    # Capture the initial folder dump
                    if memory_id not in self.mem_ids_dumps_dict:
                        self.mem_ids_dumps_dict[memory_id] = dump_folder(memory_id)
                    
                    # Reset the specific memory to its original state
                    success = reset_memory_for_episode(memory_id)
                    if not success:
                        print(f"❌ Warning: Failed to reset memory {memory_id}")
                else:
                    print("⚠️  Warning: No memory ID found in label")
                        
            except Exception as e:
                print(f"Warning: Could not extract memory ID from label: {e}")
        
        
        return {"observation": states["observation"]}

    async def step(self, states: dict, **kwargs) -> Dict[str, Any]:
        """Execute one step of the agent interaction

        Args:
            states: Dictionary containing observation_text, action_text, and label

        Returns:
            Dict[str, Any]: A dictionary containing:
                - rewards: Reward value for advantage calculation
                - scores: Reward value for dynamic filtering
                - environment_feedback: The environment feedback text
                - done: Boolean indicating if the episode is complete
                - sampling_params: Parameters for vLLM sampling
                - extra_logs: Additional logging information
        """
        print(f"step_idx: {self.step_idx}, max_steps: {self.max_steps}")

        if self.step_idx >= self.max_steps:
            done = True
            environment_feedback = (
                "\n [WARNING] You have reached the maximum number of steps."
            )
            return {
                "rewards": torch.tensor(-0.1),
                "scores": torch.tensor(-0.1),
                "environment_feedback": environment_feedback,
                "done": done,
                "sampling_params": kwargs.get("sampling_params", None),
                "extra_logs": {},
            }

        observation_text = states["observation_text"]
        action_text = states["action_text"]
        label = states["label"]

        # Remove all the <think> blocks except the last one
        observation = remove_all_thinks_except_last(observation_text)
        #observation = observation_text
        
        # Truncate the action after the closing tags
        # This preserves all action blocks (including empty ones) by finding the last closing tag
        action = action_text
        
        # Find the positions of both closing tags
        python_end_pos = -1
        reply_end_pos = -1
        
        if "</python>" in action:
            python_end_pos = action.find("</python>") + len("</python>")
            
        if "</reply>" in action:
            reply_end_pos = action.find("</reply>") + len("</reply>")
        
        # Truncate at the position of whichever tag appears last
        # This ensures both blocks are preserved, even if one is empty
        if python_end_pos > 0 or reply_end_pos > 0:
            truncate_pos = max(python_end_pos, reply_end_pos)
            action = action[:truncate_pos]

        # Extract the python code and reply
        python_code = extract_python_code(action)
        reply = extract_reply(action)
        thoughts = extract_thoughts(action)

        # Extract the task from the label
        task: Task = extract_task_from_label(label)

        # Select the appropriate reply reward calculator based on task type
        if task.task_type == TaskType.RETRIEVAL:
            reply_reward_calculator = calculate_retrieval_reply_reward
        elif task.task_type == TaskType.UPDATE:
            reply_reward_calculator = calculate_update_reply_reward
        else:
            if task.task_type == TaskType.CLARIFICATION:
                reply_reward_calculator = calculate_clarification_reply_reward
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

        # Process the action using the shared base function
        reward, done, next_observation = process_action_base(
            observation=observation,
            action=action,
            python_code=python_code,
            reply=reply,
            thoughts=thoughts,
            task=task,
            thoughts_min_length=THOUGHTS_MIN_LENGTH,
            step_num=self.step_idx,
            reply_reward_calculator=reply_reward_calculator,
            mem_ids_dumps_dict=self.mem_ids_dumps_dict
        )
            
        self.step_idx += 1
        reward = torch.tensor(reward, dtype=torch.float32)

        # Environment feedback is the difference between next_observation and current observation+action
        environment_feedback = next_observation[len(observation + action):]

        # Sampling parameters
        sampling_params = kwargs.get("sampling_params", None)
        if sampling_params is None:
            sampling_params = SamplingParams(stop=["<result>"])
        sampling_params.stop = ["<result>"]

        return {
            "rewards": reward,
            "scores": reward,
            "environment_feedback": environment_feedback,
            "done": done,
            "sampling_params": sampling_params,
            "extra_logs": {},
        }


class AgentExecutor(AgentExecutorBase):
    def __init__(self, max_steps, max_length, llm_engine, hf_tokenizer, result_queue):
        super().__init__(AgentInstance, max_steps, max_length, llm_engine, hf_tokenizer, result_queue)

    async def execute(self, prompt, label, sampling_params):
        # You can override the execute function to add custom agent running logic
        return await super().execute(prompt, label, sampling_params)
    