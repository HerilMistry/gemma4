"""
Sanctuary 3.0 — DPO Trainer (Unsloth)
Aligns Gemma using Direct Preference Optimization.
Memory-optimized for local/federated training.
"""

import os
import torch
from unsloth import FastLanguageModel, PatchDPOTrainer
from trl import DPOTrainer
from transformers import TrainingArguments
from federated.client_utils import extract_preference_pairs, prepare_dpo_dataset

# Patch for DPO support in Unsloth
PatchDPOTrainer()

def train_dpo():
    # --- 1. Load Model & Tokenizer ---
    max_seq_length = 2048
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/gemma-2b-it-bnb-4bit",
        max_seq_length = max_seq_length,
        load_in_4bit = True,
    )

    # Add LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha = 32,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
    )

    # --- 2. Load Local Data ---
    pairs = extract_preference_pairs()
    if not pairs:
        print("No preference pairs found in Vault. Adding dummy example for structure validation.")
        pairs = [{
            "prompt": "I feel like a failure.",
            "chosen": "I'm sorry you're feeling this way. It's common to feel like a 'failure' when we're under stress, but this is often an overgeneralization. What's one small thing you did today that you're proud of?",
            "rejected": "You are not a failure, stop thinking that."
        }]
    
    dataset = prepare_dpo_dataset(pairs)

    # --- 3. DPO Training Loop ---
    dpo_trainer = DPOTrainer(
        model = model,
        ref_model = None, # Unsloth handles ref_model internally to save VRAM
        args = TrainingArguments(
            per_device_train_batch_size = 2,
            gradient_accumulation_steps = 4,
            warmup_ratio = 0.1,
            num_train_epochs = 1,
            learning_rate = 5e-5,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.0,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "dpo_outputs",
        ),
        beta = 0.1, # DPO temperature
        train_dataset = dataset,
        tokenizer = tokenizer,
        max_length = max_seq_length,
        max_prompt_length = 512,
    )

    print("Starting DPO training...")
    dpo_trainer.train()
    print("DPO training complete.")

    # --- 4. Export LoRA Weights for Federated Aggregation ---
    lora_path = "lora_updates/local_update"
    model.save_pretrained(lora_path)
    print(f"LoRA weights exported to {lora_path}. Ready for federated aggregation.")

if __name__ == "__main__":
    train_dpo()
