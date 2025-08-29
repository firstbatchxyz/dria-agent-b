# Experiment 4

## Comments

The difference between this experiment and the last one is that we added clarification data & task and retrieval with filters.

- Wandb: https://wandb.ai/firstbatchxyz/obsidian-retrieval-openrlhf/runs/zcvsz7sc?nw=nwuseratakant

HF
- Untrained Model: [Qwen/Qwen3-4B-Thinking-2507](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507)
- Step 12: [driaforall/qwen3-4b-think-2507-exp4-step12](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp4-step12)
- Step 16: [driaforall/qwen3-4b-think-2507-exp4-step16](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp4-step16)
- Step 23: [driaforall/qwen3-4b-think-2507-exp4-step23](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp4-step23)
- Step 35: [driaforall/qwen3-4b-think-2507-exp4-step35](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp4-step35)
- Step 39: [driaforall/qwen3-4b-think-2507-exp4-step39](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp4-step39)
- Step 66: [driaforall/qwen3-4b-think-2507-exp4-step66](https://huggingface.co/driaforall/qwen3-4b-think-2507-exp4-step66)
## Eval Scores (o3 judge)
| Step | Retrieval | Update | Clarification | Filter | Overall | Training Score |
|-------|-----------|--------|---------------|--------|---------|------|
| 0 | 0.4545 | 0 | 0.2727 | 0.75 | 0.3929 | - |
| 12 | 0.545 | 0.1818 | 0.2727 | 0.9167 | 0.5 | 0.2856 |
| 16 | 0.5909 | 0.2727 | 0.3636 | 0.75 | 0.5179 | 0.4815 |
| 23 | 0.7727 | 0.4545 | 0.4545 | 1 | 0.6964 | 0.5843 |
| 35 | 0.8636 | 0.6363 | 0.4545 | 0.9167 | 0.75 | 0.7049 |
| 39 | 0.8636 | 0.7272 | 0.3636 | 0.9167 | 0.75 | 0.8096 |
| 66 | 0.5909 | 0.3636 | 0.2727 | 0.5 | 0.4643 | 0.9116 |


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
    "max_epochs": 1,
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
```