# mem-agent

Repository for the paper "mem-agent: Equipping LLM Agents with Memory Using RL".

## Setup

1. Copy environment file:

   ```bash
   make copy-env
   ```

   and add the relevant values w.r.t. what you want to do in the repo. The `OPENAI_API_KEY`, `WANDB_API_KEY` and `WANDB_PROJECT` are required for training and the `OPENROUTER_API_KEY` is required for evaluation.

2. Check if uv is installed and install if needed:

   ```bash
   make check-uv
   ```

3. Install dependencies (root and agent project):

   ```bash
   make install
   ```

## Training

1. Prepare memory from instances:

   ```bash
   make setup-memory
   ```

2. **IMPORTANT**: For the training of Qwen2.5 and upwards, use this make target to remove a potential error vLLM might throw mid-training:

   ```bash
   make remove-vllm-error
   ```

3. Review configuration:

   - Edit `config.json` to adjust model and hyperparameters.

4. Start training:

   ```bash
   make train
   ```

Notes:
- On macOS, GPU-specific packages are automatically skipped during install and train.

## Evaluation

Runnign the evaluation is very simple, uses OpenRouter by default and thus accepts OpenRouter model names.

```bash
# Basic (set your preferred model)
make eval MODEL=qwen/qwen3-8b

# Use vLLM or LMStudio for local inference
make eval MODEL=qwen/qwen3-8b USE_VLLM=1
```

Evaluation reads data from `data/eval/`.
