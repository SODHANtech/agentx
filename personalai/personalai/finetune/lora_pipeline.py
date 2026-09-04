import json
from pathlib import Path
from typing import Dict, Any, List


class ChatMLFormatter:
    """Formats raw tool dataset examples into standard ChatML / Hermès prompt templates for QLoRA fine-tuning."""

    @staticmethod
    def format_tool_call_sample(
        system_instruction: str,
        user_message: str,
        tool_call: Dict[str, Any],
        tool_response: str,
        final_answer: str,
    ) -> Dict[str, Any]:
        """Formats a tool invocation conversation step into ChatML JSONL format."""
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": f"<tool_call>\n{json.dumps(tool_call)}\n</tool_call>"},
            {"role": "tool", "content": tool_response},
            {"role": "assistant", "content": final_answer},
        ]
        return {"messages": messages}


class FineTuneConfigGenerator:
    """Generates Unsloth / PEFT QLoRA fine-tuning configuration specifications."""

    @staticmethod
    def generate_unsloth_script(
        model_name: str = "unsloth/Meta-Llama-3.1-8B-Instruct",
        dataset_path: str = "data/tool_dataset.jsonl",
        output_dir: str = "adapters/personal_ai_lora",
        max_seq_length: int = 4096,
        r: int = 16,
        lora_alpha: int = 16,
    ) -> str:
        """Generates a complete Python training script using Unsloth for QLoRA fine-tuning."""
        script = f'''# QLoRA Fine-Tuning Script with Unsloth for Tool Calling & Agentic Behavior
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

max_seq_length = {max_seq_length}
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="{model_name}",
    max_seq_length=max_seq_length,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r={r},
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha={lora_alpha},
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

dataset = load_dataset("json", data_files="{dataset_path}")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="{output_dir}",
    ),
)

trainer_stats = trainer.train()
model.save_pretrained_merged("{output_dir}_GGUF", tokenizer, save_method="merged_16bit")
print("Fine-tuning completed. LoRA adapter saved to {output_dir}")
'''
        return script
