# Set default target
.DEFAULT_GOAL := help

include .env

# Help command
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  1. help - Show this help message"
	@echo "  2. check-uv - Check if uv is installed and install if needed"
	@echo "  3. install - Install dependencies using uv"
	@echo "  4. setup-memory - Setup memory from instances"
	@echo "  5. remove-vllm-error - Remove vllm error check"
	@echo "  6. train - Run the training script"

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

# Run the training script
train:
	@echo "Starting training..."
	chmod +x train_agent.sh
	WANDB_API_KEY=$(WANDB_API_KEY) ./train_agent.sh
