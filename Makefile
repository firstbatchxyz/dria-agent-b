# Set default target
.DEFAULT_GOAL := help

include .env

# Training mode variables
MODE ?= mixed

# Evaluation variables
MODEL ?= qwen/qwen3-8b
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
	@echo "  6. format-data - Format dataset with mixed mode → data/openrlhf/mixed/"
	@echo "  10. train - Run training with mixed mode"
	@echo "  11. eval - Run evaluation on QA datasets"
	@echo ""
	@echo "Training mode variables:"
	@echo "  MODE - Set training mode (mixed, ordered, one-category)"
	@echo "  CATEGORY - Set category for one-category mode (retrieval, update)"
	@echo "  Usage: make train MODE=ordered"
	@echo "         make train MODE=one-category CATEGORY=update"
	@echo ""
	@echo "Evaluation variables:"
	@echo "  MODEL - Model name for agent (default: qwen/qwen3-8b)"
	@echo "  USE_VLLM - Set to any value to use vLLM for inference"
	@echo "  ADD_THINK - Set to any value to add '/think' suffix to prompts"
	@echo "  Usage: make eval MODEL=qwen/qwen3-8b"
	@echo "         make eval USE_VLLM=1 ADD_THINK=1"

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

# Format dataset with different modes
format-data:
	@echo "Formatting dataset with mixed mode (default)..."
	uv run --project agent python training/scripts/format_dataset.py --mode mixed

# Run the training script with mode support
train:
	@echo "Starting training with mode: $(MODE)..."
	@if [ "$(MODE)" = "one-category" ]; then \
		echo "Using category: $(CATEGORY)"; \
		export PROMPT_DATA_PATH="data/openrlhf/one-category/$(CATEGORY)"; \
	else \
		export PROMPT_DATA_PATH="data/openrlhf/$(MODE)"; \
	fi; \
	chmod +x train_agent.sh; \
	WANDB_API_KEY=$(WANDB_API_KEY) PROMPT_DATA_PATH=$$PROMPT_DATA_PATH ./train_agent.sh


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
	echo "Running: uv run --project agent evaluation/evaluate.py $$EVAL_ARGS"; \
	uv run --project agent evaluation/evaluate.py $$EVAL_ARGS
