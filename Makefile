# Set default target
.DEFAULT_GOAL := help

include .env

# Evaluation variables
USE_VLLM ?= 
ADD_THINK ?=

# Help command
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  1. help - Show this help message"
	@echo "  2. check-uv - Check if uv is installed and install if needed"
	@echo "  3. install - Install dependencies using uv"
	@echo "  4. setup-memory - Setup memory from instances"
	@echo "  5. remove-vllm-error - Remove vllm error check"
	@echo "  6. format-data - Format dataset → data/openrlhf/mixed/"
	@echo "  7. add-filters - Add filters to 50% of retrieval records in data/openrlhf/mixed"
	@echo "  8. gen-clarification - Generate clarification samples from instances"
	@echo "  9. sync-mixed-prompt - Sync mixed dataset system prompt from agent/system_prompt.txt"
	@echo "  10. train - Run training"
	@echo "  11. eval - Run evaluation on QA datasets"
	@echo "  12. mcp-serve - Start the MCP server"
	@echo ""
	@echo "Evaluation variables:"
	@echo "  MODEL - Model name for agent (default: qwen/qwen3-8b)"
	@echo "  USE_VLLM - Set to any value to use vLLM for inference"
	@echo "  ADD_THINK - Set to any value to add '/think' suffix to prompts"
	@echo "  Usage: make eval MODEL=qwen/qwen3-8b"
	@echo "         make eval USE_VLLM=1 ADD_THINK=1"
	@echo "         make mcp-serve MCP_HOST=127.0.0.1 MCP_PORT=8765"

# Check if uv is installed and install if needed
check-uv:
	@echo "Checking if uv is installed..."
	@if ! command -v uv > /dev/null; then \
		echo "uv not found. Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "Please restart your shell or run 'source ~/.bashrc' (or ~/.zshrc) to use uv"; \
	else \
		echo "uv is already installed"; \
		uv --version; \
	fi

install: 
	sudo apt install ninja-build
	uv sync
	uv pip install --no-build-isolation openrlhf[vllm]
	uv pip install liger-kernel>=0.3.0
	@echo "Checking if ninja is installed..."
	@if ! uv pip freeze | grep -q "^ninja=="; then \
		echo "ninja not found. Installing ninja..."; \
		uv pip install ninja; \
	else \
		echo "ninja is already installed"; \
	fi
	@echo "Ensuring black is installed..."
	@if ! uv pip freeze | grep -q "^black=="; then \
		echo "black not found. Installing black..."; \
		uv pip install black; \
	else \
		echo "black is already installed"; \
	fi
	@echo "Installing agent environment..."
	cd agent && uv sync && cd ..

setup-memory:
	uv run --project agent python training/scripts/setup_memory.py

remove-vllm-error:
	python3 remove_vllm_error.py

# Format dataset
format-data:
	@echo "Formatting dataset..."
	uv run --project agent python training/scripts/format_dataset.py --mode mixed

# Add filters to half of retrieval questions in mixed train/valid
add-filters:
	@echo "Adding filters to 50% of retrieval records in data/openrlhf/mixed..."
	@ARGS=""; \
	if [ -n "$(CONCURRENCY)" ]; then \
		ARGS="$$ARGS --concurrency $(CONCURRENCY)"; \
	fi; \
	if [ -n "$(FRACTION)" ]; then \
		ARGS="$$ARGS --fraction $(FRACTION)"; \
	fi; \
	if [ -n "$(SEED)" ]; then \
		ARGS="$$ARGS --seed $(SEED)"; \
	fi; \
	if [ -n "$(FILTER_MODEL)" ]; then \
		ARGS="$$ARGS --model $(FILTER_MODEL)"; \
	fi; \
	uv run --project agent python data_gen/generate_filters.py --dataset-dir data/openrlhf/mixed --instances-dir data/instances $$ARGS

# Generate clarification dataset (one-category/clarification)
gen-clarification:
	@echo "Generating clarification dataset from instances..."
	@ARGS=""; \
	if [ -n "$(CONCURRENCY)" ]; then \
		ARGS="$$ARGS --concurrency $(CONCURRENCY)"; \
	fi; \
	if [ -n "$(SEED)" ]; then \
		ARGS="$$ARGS --seed $(SEED)"; \
	fi; \
	if [ -n "$(LIMIT)" ]; then \
		ARGS="$$ARGS --limit-memories $(LIMIT)"; \
	fi; \
	if [ -n "$(MODEL)" ]; then \
		ARGS="$$ARGS --model $(MODEL)"; \
	fi; \
	if [ -n "$(PER_TYPE)" ]; then \
		ARGS="$$ARGS --per-type $(PER_TYPE)"; \
	fi; \
	if [ -n "$(KINDS)" ]; then \
		ARGS="$$ARGS --kinds $(KINDS)"; \
	fi; \
	if [ -n "$(MIX_IN_DATA)" ]; then \
		ARGS="$$ARGS --mix-in-data"; \
	fi; \
	uv run --project agent python data_gen/generate_clarifcation.py $$ARGS

# Sync mixed dataset system prompt from latest file
sync-mixed-prompt:
	@echo "Syncing system prompt into data/openrlhf/mixed/{train,valid}.jsonl" 
	uv run --project agent python training/scripts/update_system_prompt_in_dataset.py --dataset-dir data/openrlhf/mixed --prompt-file agent/system_prompt.txt

# Run the training script
train:
	uv pip install --no-build-isolation openrlhf[vllm]
	uv pip install liger-kernel>=0.3.0
	python3 remove_vllm_error.py
	@echo "Starting training..."
	chmod +x train_agent.sh
	WANDB_API_KEY=$(WANDB_API_KEY) ./train_agent.sh


# Evaluation target
eval:
	@echo "Starting evaluation with model: $(MODEL)..."
	@EVAL_ARGS="--model $(MODEL)"; \
	if [ -n "$(USE_VLLM)" ]; then \
		EVAL_ARGS="$$EVAL_ARGS --use-vllm"; \
		echo "Using vLLM for inference"; \
	fi; \
	if [ -n "$(ADD_THINK)" ]; then \
		EVAL_ARGS="$$EVAL_ARGS --add-think"; \
		echo "Adding '/think' suffix to prompts"; \
	fi; \
	cd evaluation && uv sync && cd ..; \
	echo "Running: uv run --project evaluation evaluation/evaluate.py $$EVAL_ARGS"; \
	uv run --project evaluation evaluation/evaluate.py $$EVAL_ARGS --data-dir data/eval

run-agent:
	uv run vllm serve driaforall/mem-agent

mcp-serve:
	@echo "Starting MCP server..."
	@echo "Syncing top-level dependencies..."
	uv sync
	MCP_HOST=$(MCP_HOST) MCP_PORT=$(MCP_PORT) MCP_TRANSPORT=$(MCP_TRANSPORT) uv run python -m mcp_server.server
