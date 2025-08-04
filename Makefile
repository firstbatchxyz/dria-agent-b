# Set default target
.DEFAULT_GOAL := help

include .env

# Training mode variables
MODE ?= mixed
CATEGORY ?= retrieval

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
	@echo "  7. format-data-ordered - Format dataset with ordered mode → data/openrlhf/ordered/"
	@echo "  8. format-data-retrieval-only - Format dataset with retrieval only → data/openrlhf/one-category/retrieval/"
	@echo "  9. format-data-update-only - Format dataset with update only → data/openrlhf/one-category/update/"
	@echo "  10. train - Run training with mixed mode (default)"
	@echo "  11. train-mixed - Run training with mixed mode"
	@echo "  12. train-ordered - Run training with ordered mode" 
	@echo "  13. train-retrieval-only - Run training with retrieval data only"
	@echo "  14. train-update-only - Run training with update data only"
	@echo ""
	@echo "Training mode variables:"
	@echo "  MODE - Set training mode (mixed, ordered, one-category)"
	@echo "  CATEGORY - Set category for one-category mode (retrieval, update)"
	@echo "  Usage: make train MODE=ordered"
	@echo "         make train MODE=one-category CATEGORY=update"

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
	uv run --project agent python setup_memory.py

remove-vllm-error:
	python3 remove_vllm_error.py

# Format dataset with different modes
format-data:
	@echo "Formatting dataset with mixed mode (default)..."
	uv run --project agent python format_dataset.py --mode mixed

format-data-ordered:
	@echo "Formatting dataset with ordered mode (retrieval first, then update)..."
	uv run --project agent python format_dataset.py --mode ordered

format-data-retrieval-only:
	@echo "Formatting dataset with retrieval data only..."
	uv run --project agent python format_dataset.py --mode one-category --category retrieval

format-data-update-only:
	@echo "Formatting dataset with update data only..."
	uv run --project agent python format_dataset.py --mode one-category --category update

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

# Training targets for different modes
train-mixed:
	@$(MAKE) train MODE=mixed

train-ordered:
	@$(MAKE) train MODE=ordered

train-retrieval-only:
	@$(MAKE) train MODE=one-category CATEGORY=retrieval

train-update-only:
	@$(MAKE) train MODE=one-category CATEGORY=update
