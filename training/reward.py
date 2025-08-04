from pathlib import Path
import os
import uuid
import json

from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from training import OBSIDIAN_ROOT

load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RETRIEVAL_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "retrieval_judge_prompt.txt")
UPDATE_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "update_judge_prompt.txt")
GPT_O3 = "o3-2025-04-16"
DEBUG_DIR = os.path.join(OBSIDIAN_ROOT, "debug")
DEBUG_JUDGE_DIR = os.path.join(DEBUG_DIR, "judge")
os.makedirs(DEBUG_JUDGE_DIR, exist_ok=True)

class RetrievalJudgeResponse(BaseModel):
    question: str
    reply: str
    ground_truth: str
    reasoning: str
    ground_truth_in_reply: bool

class UpdateJudgeResponse(BaseModel):
    num_correct_diffs_applied: int
    num_target_diffs: int

def load_retrieval_judge_prompt(question: str, reply: str, ground_truth: str) -> str:
    """
    Load the retrieval judge prompt and replace the placeholders with the reply and ground truth.
    """
    try:
        with open(RETRIEVAL_JUDGE_PROMPT_PATH, "r") as f:
            judge_prompt = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Judge prompt file not found at {RETRIEVAL_JUDGE_PROMPT_PATH}")
    
    judge_prompt = judge_prompt.replace("{{question}}", question)
    judge_prompt = judge_prompt.replace("{{reply}}", reply)
    judge_prompt = judge_prompt.replace("{{ground_truth}}", ground_truth)
    return judge_prompt

def load_update_judge_prompt(python_blocks: str, diff: str) -> str:
    """
    Load the update judge prompt and replace the placeholders with the python blocks and diff.
    """
    try:
        with open(UPDATE_JUDGE_PROMPT_PATH, "r") as f:
            judge_prompt = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Judge prompt file not found at {UPDATE_JUDGE_PROMPT_PATH}")
    
    judge_prompt = judge_prompt.replace("{{python_blocks}}", python_blocks)
    judge_prompt = judge_prompt.replace("{{diff}}", diff)
    return judge_prompt

def get_model_response(schema: BaseModel, prompt: str, model: str) -> BaseModel:
    """
    Get a structured response from the OpenAI model

    Args:
        schema: The schema of the response
        prompt: The prompt to send to the model
        model: The model to use

    Returns:
        The structured response
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    for attempt in range(3):
        try:
            response = client.responses.parse(
                model=model,
                input=[
                    {"role": "user", "content": prompt}
                ],
                text_format=schema
            )
            return response.output_parsed 
        except Exception as e:
            print(f"OpenAI call failed on attempt {attempt + 1}: {e}")
            if attempt == 2:  # Last attempt
                print("All retry attempts failed")
                return None

def get_retrieval_reward(
        question: str,
        agent_reply: str,
        ground_truth: str,
        debug: bool = False
    ) -> float:
    """
    Get the reward for the given agent reply and ground truth.

    Args:
        question: The question to evaluate
        agent_reply: The agent's reply to the question
        ground_truth: The ground truth answer
        debug: Whether to save the debug files

    Returns:
        float: 1.0 if ground truth is present in reply, 0.0 otherwise
    """
    judge_prompt = load_retrieval_judge_prompt(question, agent_reply, ground_truth)
    judge_response = get_model_response(
        schema=RetrievalJudgeResponse,
        prompt=judge_prompt,
        model=GPT_O3
    )

    if debug:
        debug_id = str(uuid.uuid4())
        debug_file = os.path.join(DEBUG_JUDGE_DIR, f"retrieval_judge_response_{debug_id}.json")
        try:
            with open(debug_file, "w") as f:
                json.dump(judge_response.model_dump(), f)
        except Exception as e:
            print(f"Error saving debug file: {e}")
            
    if judge_response is None:
        return 0.0
    return 1.0 if judge_response.ground_truth_in_reply else 0.0

def get_update_reward(
        python_blocks: str,
        diff: str,
        debug: bool = False
    ) -> float:
    """
    Get the reward for the given python blocks and diff.

    Args:
        python_blocks: The python blocks to evaluate
        diff: The diff to evaluate
        debug: Whether to save the debug files

    Returns:
        float: The reward for the given python blocks and diff
    """
    judge_prompt = load_update_judge_prompt(python_blocks, diff)
    judge_response = get_model_response(
        schema=UpdateJudgeResponse,
        prompt=judge_prompt,
        model=GPT_O3
    )

    if judge_response is None:
        return 0.0
    if judge_response.num_target_diffs == 0:
        retries = 3
        for _ in range(retries):
            judge_response = get_model_response(
                schema=UpdateJudgeResponse,
                prompt=judge_prompt,
                model=GPT_O3
            )
            if judge_response is not None and judge_response.num_target_diffs > 0:
                break

    if debug:
        debug_id = str(uuid.uuid4())
        debug_file = os.path.join(DEBUG_JUDGE_DIR, f"update_judge_response_{debug_id}.json")
        try:
            with open(debug_file, "w") as f:
                json.dump(judge_response.model_dump(), f)
        except Exception as e:
            print(f"Error saving debug file: {e}")
        
    return judge_response.num_correct_diffs_applied / judge_response.num_target_diffs if judge_response is not None else 0.0