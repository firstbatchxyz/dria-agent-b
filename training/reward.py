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
RETRIEVAL_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "retrieval_judge_prompt.txt")
UPDATE_JUDGE_PROMPT_PATH = os.path.join(OBSIDIAN_ROOT, "training", "prompts", "update_judge_prompt.txt")

# Use OpenRouter Gemini to align with agent/evaluation
OPENROUTER_GEMINI = os.getenv("JUDGE_MODEL", "google/gemini-2.5-pro")

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
    reasoning: str
    success: bool

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

def _extract_first_json_object(text: str) -> dict | None:
    """Extract the first JSON object from arbitrary text and return as dict."""
    if not text:
        return None
    # Fast path: trim code fences
    if "```" in text:
        try:
            segment = text.split("```", 1)[1]
            # If a language tag exists, split again
            if "\n" in segment:
                segment = segment.split("\n", 1)[1]
            candidate = segment.split("```", 1)[0]
            return json.loads(candidate)
        except Exception:
            pass
    # General scan for a JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return None
    return None


def get_model_response(schema: BaseModel, prompt: str, model: str = OPENROUTER_GEMINI) -> BaseModel | None:
    """
    Get a structured response using OpenRouter's OpenAI-compatible Chat Completions.

    The judge prompts already enforce a strict JSON output; we parse JSON and
    validate it against the provided Pydantic schema.
    """
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = completion.choices[0].message.content or ""
            data = _extract_first_json_object(content)
            if data is None:
                # Try a best-effort fallback: wrap as JSON if exact keys are found
                # This helps when model responds with key: value lines
                try:
                    # crude normalization
                    cleaned = content.strip()
                    data = json.loads(cleaned)
                except Exception:
                    pass
            if data is None:
                raise ValueError("Model did not return valid JSON")
            return schema.model_validate(data)
        except Exception as e:
            print(f"OpenRouter call/parse failed on attempt {attempt + 1}: {e}")
            if attempt == 2:
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
        model=OPENROUTER_GEMINI
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
        model=OPENROUTER_GEMINI
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