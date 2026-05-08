import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset, Dataset, concatenate_datasets
from trl import SFTTrainer
from transformers import TrainingArguments, EarlyStoppingCallback
import pandas as pd
import os

# --- 1. Configuration & Model Loading ---
max_seq_length = 2048
dtype = None
load_in_4bit = True

print("Loading Base Gemma Model...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/gemma-2b-it-bnb-4bit", 
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# --- 2. Apply LoRA Adapters ---
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 32, 
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

# --- 3. Data Blending & Cleaning ---
print("Loading and Blending Datasets...")
datasets_to_merge = []

# Dataset A: Empathetic Dialogues 
try:
    emp_df = pd.read_csv('/kaggle/input/datasets/atharvjairath/empathetic-dialogues-facebook-ai/emotion-emotion_69k.csv')
    emp_df['instruction'] = "You are Sanctuary, a CBT shadow. Listen and respond with empathy."
    emp_df['text'] = emp_df['Situation'] 
    emp_df['label'] = emp_df['empathetic_dialogues'] 
    emp_df = emp_df[['instruction', 'text', 'label']].dropna()
    
    if len(emp_df) > 3000:
        emp_df = emp_df.sample(n=3000, random_state=42)
        
    emp_dataset = Dataset.from_pandas(emp_df)
    datasets_to_merge.append(emp_dataset)
    print(f"Loaded Empathetic Dialogues (Balanced to {len(emp_df)} rows).")
except Exception as e:
    print(f"Empathetic dataset failed to load. Error: {e}")

# Dataset B: Cognitive Distortions
try:
    annotated_df = pd.read_csv('/kaggle/input/datasets/sagarikashreevastava/cognitive-distortion-detetction-dataset/Annotated_data.csv')
    therapist_df = pd.read_csv('/kaggle/input/datasets/sagarikashreevastava/cognitive-distortion-detetction-dataset/Therapist_responses.csv')
    
    annotated_df.columns = annotated_df.columns.str.strip()
    therapist_df.columns = therapist_df.columns.str.strip()
    
    cbt_df = pd.merge(annotated_df, therapist_df, on='Id_Number', how='inner')
    
    cbt_df['instruction'] = "You are Sanctuary, a CBT shadow. Identify the cognitive distortion and provide a therapeutic Socratic response."
    cbt_df['text'] = cbt_df['Patient Question'] 
    cbt_df['label'] = "Detected Distortion: " + cbt_df['Dominant Distortion'] + "\n\nSanctuary Response: " + cbt_df['Answer']
    
    cbt_df = cbt_df[['instruction', 'text', 'label']].dropna()
    cbt_dataset = Dataset.from_pandas(cbt_df)
    datasets_to_merge.append(cbt_dataset)
    print(f"Loaded Cognitive Distortions (Merged {len(cbt_df)} rows).")
except Exception as e:
    print(f"Cognitive Distortions failed to load. Error: {e}")

if not datasets_to_merge:
    raise ValueError("Critical Error: No datasets loaded. Halting script.")

merged_dataset = concatenate_datasets(datasets_to_merge)

# --- 4. Gemma Formatting & Verification Split ---
EOS_TOKEN = tokenizer.eos_token 

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["text"]
    outputs      = examples["label"]
    
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        gemma_prompt = (
            f"<start_of_turn>user\n"
            f"{instruction}\n\n"
            f"User input: {input_text}<end_of_turn>\n"
            f"<start_of_turn>model\n"
            f"{output}<end_of_turn>{EOS_TOKEN}"
        )
        texts.append(gemma_prompt)
    return { "text" : texts }

mapped_dataset = merged_dataset.map(formatting_prompts_func, batched = True)

print("Splitting data into Training (90%) and Validation (10%)...")
split_dataset = mapped_dataset.train_test_split(test_size=0.1, seed=42)

# --- 5. The Training Loop (Stable 4.x API) ---
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,               # <--- LOCKED: No quotes, using standard tokenizer
    train_dataset = split_dataset["train"], 
    eval_dataset = split_dataset["test"],   
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, 
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10,
        num_train_epochs = 3, 
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 10, 
        
        lr_scheduler_type = "cosine",        
        eval_strategy = "steps",       # <--- LOCKED: Standard evaluation_strategy
        eval_steps = 20,                     
        save_strategy = "steps",             
        save_steps = 20,
        load_best_model_at_end = True,       
        metric_for_best_model = "eval_loss", 
        
        optim = "adamw_8bit",
        weight_decay = 0.01,
        seed = 3407,
        output_dir = "outputs",
    ),
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)

print("Igniting SFT Trainer...")
trainer_stats = trainer.train()

# --- 6. Export to GGUF (Kaggle Fix) ---
print("Training complete. Pre-configuring llama.cpp to bypass Kaggle network blocks...")

# Kaggle blocks the internal 'ping' command Unsloth uses to check for internet.
# This causes Unsloth to crash when trying to download llama.cpp for GGUF conversion.
# We bypass this by manually cloning it exactly where Unsloth expects it.
import os
os.system("mkdir -p /root/.unsloth")
if not os.path.exists("/root/.unsloth/llama.cpp"):
    print("Cloning llama.cpp manually...")
    os.system("git clone https://github.com/ggerganov/llama.cpp /root/.unsloth/llama.cpp")

print("Exporting model as GGUF for Ollama edge deployment...")
model.save_pretrained_gguf("sanctuary_gemma4_cbt", tokenizer, quantization_method = "q4_k_m")
print("Export complete. Download sanctuary_gemma4_cbt-unsloth.Q4_K_M.gguf from the Kaggle output directory.")