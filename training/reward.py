from pathlib import Path
import os
import uuid
import json

from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from training import OBSIDIAN_ROOT
from agent.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RETRIEVAL_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "retrieval_judge_prompt.txt")
UPDATE_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "update_judge_prompt.txt")
CLARIFICATION_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "clarification_judge_prompt.txt")
GPT_O3 = "o3-2025-04-16"

# Use OpenRouter Gemini to align with agent/evaluation
OPENROUTER_GEMINI = os.getenv("JUDGE_MODEL", "google/gemini-2.5-pro")

DEBUG_DIR = os.path.join(OBSIDIAN_ROOT, "debug")
DEBUG_JUDGE_DIR = os.path.join(DEBUG_DIR, "judge")
os.makedirs(DEBUG_JUDGE_DIR, exist_ok=True)

class RetrievalJudgeResponse(BaseModel):
    reply: str
    ground_truth: str
    reasoning: str
    ground_truth_in_reply: bool

class UpdateJudgeResponse(BaseModel):
    reasoning: str
    success: bool

class ClarificationJudgeResponse(BaseModel):
    reasoning: str
    success: bool

def load_retrieval_judge_prompt(question: str, reply: str, ground_truth: str, filter_text: str | None = None) -> str:
    """
    Load the retrieval judge prompt and replace the placeholders with the reply and ground truth.
    If filter_text is provided, append an instruction block for the judge to consider the filter constraints.
    """
    try:
        with open(RETRIEVAL_JUDGE_PROMPT_PATH, "r") as f:
            judge_prompt = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Judge prompt file not found at {RETRIEVAL_JUDGE_PROMPT_PATH}")

    judge_prompt = judge_prompt.replace("{{question}}", question)
    judge_prompt = judge_prompt.replace("{{reply}}", reply)
    judge_prompt = judge_prompt.replace("{{ground_truth}}", ground_truth)

    if filter_text is not None and len(filter_text.strip()) > 0:
        filter_block = (
            "\n\nAdditional filter constraints (if present, STRICTLY enforce):\n"
            "<filter>\n" + filter_text.strip() + "\n</filter>\n"
            "Guidance: If the reply violates explicit filter constraints (e.g., reveals banned info),"
            " mark ground_truth_in_reply=false even if it includes the fact."
        )
        judge_prompt = judge_prompt + filter_block

    return judge_prompt

def load_update_judge_prompt(user_query: str, initial_folder_dump: str, final_folder_dump: str) -> str:
    """
    Load the update judge prompt from a file and format it with the provided parameters.
    
    Args:
        user_query: The original user request
        initial_folder_dump: The folder state before any actions
        final_folder_dump: The folder state after all actions
    
    Returns:
        The formatted prompt string.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = os.path.join(script_dir, "prompts", "update_judge_prompt.txt")
    
    with open(prompt_file, "r") as f:
        prompt_template = f.read()
    
    return prompt_template.replace("{{user_query}}", user_query).replace("{{initial_folder_dump}}", initial_folder_dump).replace("{{final_folder_dump}}", final_folder_dump)

def load_clarification_judge_prompt(question: str, agent_reply: str) -> str:
    """
    Load the clarification judge prompt and fill placeholders with question and reply.
    """
    try:
        with open(CLARIFICATION_JUDGE_PROMPT_PATH, "r") as f:
            template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Judge prompt file not found at {CLARIFICATION_JUDGE_PROMPT_PATH}")
    return template.replace("{{question}}", question).replace("{{reply}}", agent_reply)

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
        filter_text: str | None = None,
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
    judge_prompt = load_retrieval_judge_prompt(question, agent_reply, ground_truth, filter_text)
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
        user_query: str,
        initial_folder_dump: str,
        final_folder_dump: str,
        debug: bool = False
    ) -> float:
    """
    Get the update reward based on comparing folder states before and after actions.
    
    Args:
        user_query: The original user request
        initial_folder_dump: The folder state before any actions
        final_folder_dump: The folder state after all actions
        debug: If True, print debug information.
        
    Returns:
        1.0 if the updates were correctly applied, 0.0 otherwise.
    """
    
    # Load the prompt with the provided data
    prompt = load_update_judge_prompt(
        user_query=user_query,
        initial_folder_dump=initial_folder_dump,
        final_folder_dump=final_folder_dump
    )
    
    # Get the model response
    response = get_model_response(
        schema=UpdateJudgeResponse,
        prompt=prompt,
        model=GPT_O3
    )
    
    if debug:
        debug_id = str(uuid.uuid4())
        debug_file = os.path.join(DEBUG_JUDGE_DIR, f"update_judge_response_{debug_id}.json")
        try:
            with open(debug_file, "w") as f:
                json.dump(response.model_dump(), f)
        except Exception as e:
            print(f"Error saving debug file: {e}")
    
    # Return 1.0 if success, 0.0 otherwise
    return 1.0 if response.success else 0.0

def get_clarification_reward(
        question: str,
        agent_reply: str,
        debug: bool = False
    ) -> float:
    """
    Get the clarification reward based on whether the reply is an appropriate clarification.
    Returns 1.0 for success, 0.0 otherwise.
    """
    prompt = load_clarification_judge_prompt(question=question, agent_reply=agent_reply)
    response = get_model_response(
        schema=ClarificationJudgeResponse,
        prompt=prompt,
        model=GPT_O3
    )
    if debug and response is not None:
        debug_id = str(uuid.uuid4())
        debug_file = os.path.join(DEBUG_JUDGE_DIR, f"clarification_judge_response_{debug_id}.json")
        try:
            with open(debug_file, "w") as f:
                json.dump(response.model_dump(), f)
        except Exception as e:
            print(f"Error saving debug file: {e}")
    if response is None:
        return 0.0
    return 1.0 if response.success else 0.0