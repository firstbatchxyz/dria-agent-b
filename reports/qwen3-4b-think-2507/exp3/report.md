# Experiment 3

## Comments

The difference between this experiment and the last one is that we added clarification data & task and retrieval with filters.

- Wandb: https://wandb.ai/firstbatchxyz/obsidian-retrieval-openrlhf/runs/0a3310de?nw=nwuseratakant

HF
- Untrained Model: [Qwen/Qwen3-4B-Thinking-2507](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507)
- Step 11:  [driaforall/qwen3-4b-think-2507-exp3-step11](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp3-step11)
- Step 14:  [driaforall/qwen3-4b-think-2507-exp3-step14](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp3-step14)
- Step 16:  [driaforall/qwen3-4b-think-2507-exp3-step16](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp3-step16)
- Step 19:  [driaforall/qwen3-4b-think-2507-exp3-step19](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp3-step19)
- Step 31:  [driaforall/qwen3-4b-think-2507-exp3-step31](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp3-step31)
- Step 44:  [driaforall/qwen3-4b-think-2507-exp3-step44](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp3-step44)

## Eval Scores (o3 judge)
| Step | Retrieval | Update | Clarification | Overall | Training Score |
|-------|-----------|--------|---------------|---------|-----------|
| 0 | 0.4545 | 0 | 0.2727 | 0.2955 | - |
| 11 | 0.5455 | 0.2727 | 0.2727 | 0.4091 | 0.2708 |
| 14 | 0.6364 | 0.3636 | 0.1818 | 0.4545 | 0.3327 |
| 16 | 0.7727 | 0.1818 | 0.3636 | 0.5227 | 0.4492 |
| 19 | 0.8181 | 0.3636 | 0.2727 | 0.5681 | 0.6738 |
| 31 | 0.8181 | 0.6363 | 0.3636 | 0.6591 | 0.6624 |
| 44 | 0.7727 | 0.7272 | 0.5455 | 0.7045 | 0.8023 |

# Config

### **config.json**

```json
{
  "model": {
    "name": "Qwen/Qwen3-4B-Thinking-2507"
  },
  "hyperparameters": {
    "init_kl_coef": 0.1,
    "kl_target": 0.2,
    "kl_horizon": 256,
    "max_epochs": 2,
    "actor_learning_rate": "5e-7",
    "critic_learning_rate": "1e-6",
    "num_episodes": 8,
    "thoughts_min_length": 512,
    "advantage_estimator": "group_norm"
  }
} 
```

### **train_agent.sh**

```bash
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
   --n_samples_per_prompt 16 \
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
   --packing_samples --flash_attn \
   --wandb_project obsidian-retrieval-openrlhf \
   --eps_clip 0.1 \
   --policy_loss_type gspo \
   --use_liger_kernel 
```