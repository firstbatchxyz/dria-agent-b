# Experiment 1: No /think tokens after prompt in training

Wandb: https://wandb.ai/firstbatchxyz/obsidian-retrieval-openrlhf/runs/hk8utp1z?nw=nwuseratakant
HF: https://huggingface.co/driaforall/Qwen3-14B-exp3

## Scores
| Model | Retrieval | Update | Clarification | Overall |
|-------|-----------|--------|---------------|---------|
| Untrained (no /think) | 0.5625 | 0.0000 | 0.0909 | 0.3030 |
| Untrained (with /think) | 0.8125 | 0.1667 | 0.1818 | 0.4848 |
| Trained (no /think) | 0.8750 | 0.1667 | 0.2727 | 0.5454 |
| Trained (with /think) | 0.6250 | 0.000 | 0.1818 | 0.3636 |