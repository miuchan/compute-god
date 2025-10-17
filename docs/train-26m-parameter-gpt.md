# 26M 参数 GPT 快速训练指南

本文档总结了如何在约 2 小时内从零开始训练一个约 2600 万参数的 GPT 模型，适用于只有单张 NVIDIA A100/A6000/4090 级别 GPU 的开发者。目标模型规模与 nanoGPT 官方 `gpt-mini` 类似，适合作为从零训练 GPT 的入门案例。

## 1. 准备数据集

1. **选择小体量高质量语料**：推荐从 [TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories) 或 [The Pile: DoReMi subset](https://huggingface.co/datasets/allenai/doremi) 中挑选 200~500MB 的训练数据，保证 2 小时内可以多轮遍历。
2. **分词器**：使用 `tiktoken` 或 `sentencepiece` 训练 32k 词表。示例命令：
   ```bash
   python -m tiktoken.train --input data/train.txt --model-name mini-gpt-32k --vocab-size 32768 --out vocab.json
   ```
3. **数据切分**：按照 9:1 划分训练与验证数据，分别保存为 `train.pt` 与 `val.pt`（`torch.save` 后的整型 token 张量）。

## 2. 环境依赖

使用 `uv` 创建隔离环境：

```bash
uv python install 3.11
uv venv .venv
source .venv/bin/activate
uv pip install torch==2.2.1 torchvision --index-url https://download.pytorch.org/whl/cu121
uv pip install transformers datasets accelerate tiktoken bitsandbytes
```

## 3. 模型配置

26M 参数 GPT 可采用如下超参数：

| 超参数           | 建议值 |
|------------------|--------|
| 层数 `n_layer`    | 12     |
| 注意力头 `n_head` | 12     |
| 隐藏维度 `n_embd` | 512    |
| 序列长度 `block_size` | 512 |
| 词表大小 `vocab_size` | 32768 |
| 总参数量          | ≈26M  |

## 4. 训练脚本

新建 `train_26m_gpt.py`：

```python
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import GPT2Config, GPT2LMHeadModel, get_cosine_schedule_with_warmup


class PackedDataset(Dataset):
    def __init__(self, path: str, block_size: int):
        tokens = torch.load(path)
        self.block_size = block_size
        self.tokens = tokens[: (len(tokens) // block_size) * block_size]
        self.tokens = self.tokens.view(-1, block_size)

    def __len__(self):
        return self.tokens.size(0)

    def __getitem__(self, idx):
        x = self.tokens[idx]
        return x[:-1], x[1:]


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    block_size = 512
    train_ds = PackedDataset("train.pt", block_size + 1)
    val_ds = PackedDataset("val.pt", block_size + 1)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True, pin_memory=True)
    val_dl = DataLoader(val_ds, batch_size=32)

    config = GPT2Config(
        vocab_size=32768,
        n_positions=block_size,
        n_ctx=block_size,
        n_embd=512,
        n_layer=12,
        n_head=12,
        resid_pdrop=0.1,
        embd_pdrop=0.1,
        attn_pdrop=0.1,
    )
    model = GPT2LMHeadModel(config).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95), weight_decay=0.1)
    num_training_steps = len(train_dl) * 200
    scheduler = get_cosine_schedule_with_warmup(optimizer, num_warmup_steps=2000, num_training_steps=num_training_steps)

    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")
    model.train()
    for step, (x, y) in enumerate(train_dl, start=1):
        x, y = x.to(device), y.to(device)
        with torch.cuda.amp.autocast(device_type=device.type, dtype=torch.float16):
            outputs = model(x)
            loss = torch.nn.functional.cross_entropy(outputs.logits.view(-1, outputs.logits.size(-1)), y.view(-1))
        scaler.scale(loss).backward()
        if step % 8 == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            scheduler.step()
        if step % 100 == 0:
            print(f"step {step}: loss={loss.item():.4f}")
        if step >= num_training_steps:
            break

    torch.save(model.state_dict(), "mini-gpt26m.pt")


if __name__ == "__main__":
    main()
```

### 关键点

* **AMP + 梯度累积**：脚本示例使用 PyTorch 自动混合精度与梯度累积（`step % 8 == 0`）以在显存 24GB 左右的 GPU 上训练。
* **学习率计划**：余弦退火 + 2000 步 warmup，可根据数据规模调整。
* **检查点**：建议每 1000 步保存一次模型与优化器状态，防止训练中断。

## 5. 训练命令

```bash
python train_26m_gpt.py \
  --train train.pt \
  --val val.pt \
  --batch-size 32 \
  --grad-accum 8 \
  --lr 3e-4 \
  --max-steps 20000
```

> 若希望复用上文脚本，可将命令行参数解析加入 `argparse`。使用 `accelerate launch` 可进一步提升吞吐量。

## 6. 推理与评估

1. **困惑度**：在验证集上计算 `perplexity = exp(loss)`。
2. **采样生成**：
   ```python
   from transformers import GPT2LMHeadModel, GPT2TokenizerFast

   tokenizer = GPT2TokenizerFast.from_pretrained("./tokenizer")
   model = GPT2LMHeadModel.from_pretrained("mini-gpt26m.pt")
   prompt = "Once upon a time"
   inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
   out = model.generate(**inputs, max_new_tokens=200, temperature=0.8, top_p=0.95)
   print(tokenizer.decode(out[0]))
   ```
3. **对比基线**：与 GPT2-small 或现成 30M 模型在同一任务上的损失对比，验证收敛情况。

## 7. 附加建议

* 使用 [wandb](https://wandb.ai) 或 [tensorboard](https://www.tensorflow.org/tensorboard) 跟踪训练曲线。
* 若需进一步压缩训练时间，可：
  - 降低序列长度至 384 或 256。
  - 使用 Flash Attention 2 或 xFormers 以优化注意力算子。
  - 使用 [LoRA](https://arxiv.org/abs/2106.09685) 在现有模型上微调而非全量训练。
* 参考项目：`karpathy/nanoGPT`、`lucidrains/PaLM-rlhf-pytorch`、`transformers` 官方示例。

## 8. 训练日志模板

```text
# mini-gpt26m training log
step 0100 | loss 3.72 | ppl 41.4 | tokens/s 320k
step 0500 | loss 3.10 | ppl 22.2 | tokens/s 360k
step 1000 | loss 2.80 | ppl 16.4 | tokens/s 380k
...
```

保留训练日志有助于复现 2 小时内收敛的具体配置。
