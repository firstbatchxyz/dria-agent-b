# Experiment 1: No /think tokens after prompt in training

Wandb: https://wandb.ai/firstbatchxyz/obsidian-retrieval-openrlhf/runs/1edosetm?nw=nwuseratakant
HF: https://huggingface.co/driaforall/Qwen3-14B-best-ckpt

## Scores
| Model | Retrieval | Update | Clarification | Overall |
|-------|-----------|--------|---------------|---------|
| Untrained (no /think) | 0.5625 | 0.0000 | 0.0909 | 0.3030 |
| Untrained (with /think) | 0.8125 | 0.1667 | 0.1818 | 0.4848 |
| Trained (no /think) | 0.9375 | 0.1667 | 0.1818 | 0.5454 |
| Trained (with /think) | 0.875 | 0.1667 | 0.1818 | 0.5151 |

## Correct Examples (except retrieval)

| Model | Task | Correct Examples |
|-------|------|------------------|
| Trained (no /think) | Update | "What are my current shipping addresses?" |
| Trained (no /think) | Clarification | "What's our current ROI on the LinkedIn campaign?"<br>"The hot water seems to be taking a long time to heat up. Can you look up the manual for the water heater?" |
| Trained (/think) | Update | "What are my current shipping addresses?" |
| Trained (/think) | Clarification | "What's our current ROI on the LinkedIn campaign?" <br> "I need to order more filters." |
| Untrained (/think) | Update | "What are my current shipping addresses?" |
| Untrained (/think) | Clarification | "What's our current ROI on the LinkedIn campaign?"<br>"Can you check if the resource room is available for my AP Lit class next Tuesday?" |