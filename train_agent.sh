#!/bin/bash
set -x
export PATH="$(dirname "$0")/.venv/bin:$PATH"
export NINJA="$(dirname "$0")/.venv/bin/ninja"


# Read config from JSON file
CONFIG_FILE="$(dirname "$0")/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

# Parse JSON config using Python
CONFIG_VALUES=$(python3 -c "
import json
import sys
import os

config_file = '$CONFIG_FILE'
with open(config_file, 'r') as f:
    config = json.load(f)

# Extract hyperparameters
hp = config['hyperparameters']
model_name = config['model']['name']

# Extract model identifier (e.g., 'Qwen/Qwen2.5-Coder-7B-Instruct' -> 'qwen2.5-coder-7b-instruct')
model_id = model_name.split('/')[-1].lower().replace('-', '-')

# Hardcode data mode to mixed
data_mode = 'mixed'

# Construct dynamic path with data mode
path_suffix = f\"{model_id}-obsidian-{data_mode}-{hp['actor_learning_rate']}-{hp['critic_learning_rate']}-{hp['max_epochs']}epochs-{hp['num_episodes']}episodes\"

# Output all values as shell variables
print(f'MODEL_NAME=\"{model_name}\"')
print(f'INIT_KL_COEF={hp[\"init_kl_coef\"]}')
print(f'KL_TARGET={hp[\"kl_target\"]}')
print(f'KL_HORIZON={hp[\"kl_horizon\"]}')
print(f'MAX_EPOCHS={hp[\"max_epochs\"]}')
print(f'ACTOR_LR={hp[\"actor_learning_rate\"]}')
print(f'CRITIC_LR={hp[\"critic_learning_rate\"]}')
print(f'NUM_EPISODES={hp[\"num_episodes\"]}')
print(f'ADVANTAGE_ESTIMATOR=\"{hp[\"advantage_estimator\"]}\"')
print(f'SAVE_PATH=\"training/ckpt/{path_suffix}\"')
print(f'CKPT_PATH=\"training/ckpt/{path_suffix}\"')
")

# Evaluate the config values as shell variables
eval "$CONFIG_VALUES"

echo "Loaded configuration:"
echo "  Model: $MODEL_NAME"
echo "  Save/Checkpoint Path: $SAVE_PATH"
echo "  Hyperparameters: init_kl_coef=$INIT_KL_COEF, kl_target=$KL_TARGET, max_epochs=$MAX_EPOCHS, etc."

.venv/bin/python -m openrlhf.cli.train_ppo_ray \
   --ref_num_nodes 1 \
   --ref_num_gpus_per_node 8 \
   --actor_num_nodes 1 \
   --actor_num_gpus_per_node 8 \
   --vllm_num_engines 2 \
   --vllm_tensor_parallel_size 4 \
   --vllm_gpu_memory_utilization 0.25 \
   --colocate_all_models \
   --init_kl_coef $INIT_KL_COEF \
   --kl_target $KL_TARGET \
   --kl_horizon $KL_HORIZON \
   --gamma 0.99 \
   --kl_estimator k3 \
   --pretrain $MODEL_NAME \
   --agent_func_path training/agent_func.py \
   --save_path $SAVE_PATH \
   --ckpt_path $CKPT_PATH \
   --advantage_estimator $ADVANTAGE_ESTIMATOR \
   --save_hf_ckpt \
   --micro_train_batch_size 2 \
   --train_batch_size 32 \
   --micro_rollout_batch_size 2 \
   --rollout_batch_size 32 \
   --n_samples_per_prompt 32 \
   --max_epochs $MAX_EPOCHS \
   --prompt_max_len 4096 \
   --max_samples 100000 \
   --generate_max_len 2048 \
   --zero_stage 3 \
   --bf16 \
   --actor_learning_rate $ACTOR_LR \
   --critic_learning_rate $CRITIC_LR \
   --prompt_data json@data/openrlhf/mixed \
   --input_key context_messages \
   --label_key label \
   --apply_chat_template \
   --use_kl_loss \
   --gradient_checkpointing \
   --packing_samples \
   --vllm_sync_backend nccl \
   --enforce_eager \
   --vllm_enable_sleep \
   --deepspeed_enable_sleep \
   --use_wandb True \
   --num_episodes $NUM_EPISODES \
   --save_steps 1 \
   --packing_samples \
   --wandb_project obsidian-retrieval-openrlhf \
   --eps_clip 0.1 \
   --policy_loss_type gspo \
   --use_liger_kernel 