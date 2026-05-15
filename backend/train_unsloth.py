# 1. Force Kaggle to downgrade its built-in libraries first
# !pip install -U "transformers<5.0.0" "trl<0.9.0"
# 2. Install Unsloth and Edge computing libraries
# !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
# !pip install --no-deps xformers peft accelerate bitsandbytes

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import torch # type: ignore
from unsloth import FastLanguageModel # type: ignore
from datasets import load_dataset, Dataset, concatenate_datasets # type: ignore
from trl import SFTTrainer # type: ignore
from transformers import TrainingArguments, EarlyStoppingCallback # type: ignore
import pandas as pd

# --- 1. Configuration & Model Loading (GEMMA 4 COMPLIANT) ---
max_seq_length = 2048
dtype = None
load_in_4bit = True

print("Loading Gemma 4 E4B (Edge 4 Billion) Instruct Model...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/gemma-4-e4b-it-bnb-4bit", 
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# --- 2. Apply LoRA Adapters (HIGH CAPACITY FOR REASONING) ---
model = FastLanguageModel.get_peft_model(
    model,
    r = 32,              # High rank to capture deep CBT reasoning
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 64,     
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    use_rslora = True, # <--- THE FIX: Rank-Stabilized LoRA enabled
    loftq_config = None,
)

# --- 3. Data Blending & Cleaning (CLINICAL DATA DIET) ---
print("Loading and Blending Datasets...")
datasets_to_merge = []

# Dataset A: Empathetic Dialogues (RESTRICTED TO PREVENT DILUTION)
try:
    emp_df = pd.read_csv('/kaggle/input/datasets/atharvjairath/empathetic-dialogues-facebook-ai/emotion-emotion_69k.csv')
    emp_df['instruction'] = "You are Sanctuary, a CBT shadow. Listen and respond with empathy."
    emp_df['text'] = emp_df['Situation'] 
    emp_df['label'] = emp_df['empathetic_dialogues'] 
    emp_df = emp_df[['instruction', 'text', 'label']].dropna()
    
    if len(emp_df) > 300: # CRITICAL FIX: Slashed to 300 rows for tone only
        emp_df = emp_df.sample(n=300, random_state=42)
        
    emp_dataset = Dataset.from_pandas(emp_df)
    datasets_to_merge.append(emp_dataset)
    print(f"Loaded Empathetic Dialogues (Severely restricted to {len(emp_df)} rows).")
except Exception as e:
    print(f"Empathetic dataset failed to load. Error: {e}")

# Dataset B: Cognitive Distortions (THE CORE LOGIC ENGINE)
try:
    annotated_df = pd.read_csv('/kaggle/input/datasets/sagarikashreevastava/cognitive-distortion-detetction-dataset/Annotated_data.csv')
    therapist_df = pd.read_csv('/kaggle/input/datasets/sagarikashreevastava/cognitive-distortion-detetction-dataset/Therapist_responses.csv')
    
    annotated_df.columns = annotated_df.columns.str.strip()
    therapist_df.columns = therapist_df.columns.str.strip()
    
    cbt_df = pd.merge(annotated_df, therapist_df, on='Id_Number', how='inner')
    
    cbt_df['instruction'] = "You are Sanctuary, a strict clinical CBT shadow. Identify the cognitive distortion and provide a therapeutic Socratic response."
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

# --- 4. Gemma 4 Formatting & Verification Split ---
from unsloth.chat_templates import get_chat_template # type: ignore
tokenizer = get_chat_template(tokenizer, chat_template="gemma")

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["text"]
    outputs      = examples["label"]
    
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        messages = [
            {"role": "user", "content": f"{instruction}\n\nUser input: {input_text}"},
            {"role": "model", "content": output}
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return { "text" : texts }

mapped_dataset = merged_dataset.map(formatting_prompts_func, batched = True)
print("Splitting data into Training (90%) and Validation (10%)...")
split_dataset = mapped_dataset.train_test_split(test_size=0.1, seed=42)

# --- 5. The Training Loop (ANTI-PLATEAU PACING) ---
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = split_dataset["train"], 
    eval_dataset = split_dataset["test"],   
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, 
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        per_device_eval_batch_size = 1, # <--- SAFETY NET
        gradient_accumulation_steps = 4,
        eval_accumulation_steps = 1,    # <--- SAFETY NET
        warmup_steps = 10,
        num_train_epochs = 4,              
        learning_rate = 1e-4,              
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 10, 
        neftune_noise_alpha = 5, # <--- THE FIX: Prevents overfitting to format
        
        lr_scheduler_type = "cosine",        
        eval_strategy = "steps",       
        eval_steps = 20,                     
        save_strategy = "steps",             
        save_steps = 20,
        load_best_model_at_end = True,       
        metric_for_best_model = "eval_loss", 
        
        optim = "paged_adamw_8bit", # <--- THE FIX: Paged optimizer stops VRAM spikes
        weight_decay = 0.01,
        seed = 3407,
        output_dir = "outputs",
    ),
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

print("Igniting SFT Trainer...")
trainer_stats = trainer.train()

# --- 6. Export to GGUF (PURE HUGGINGFACE FUSION) ---
print("Bypassing Unsloth wrappers. Initiating Pure HuggingFace Fusion...")
import torch # type: ignore
from transformers import AutoModelForCausalLM, AutoTokenizer # type: ignore
from peft import PeftModel # type: ignore
import os

adapter_path = "/kaggle/working/outputs/checkpoint-" + str(trainer.state.best_model_checkpoint).split('-')[-1] if trainer.state.best_model_checkpoint else "/kaggle/working/outputs/checkpoint-" + str(trainer.state.global_step)

hf_folder = "/kaggle/working/sanctuary_hf_model"

# Step 1: Clean the GPU RAM
import gc
try:
    del model
    del trainer
except:
    pass
torch.cuda.empty_cache()
gc.collect()

# Step 2: Load the PURE 16-bit Gemma 4 E4B base model
print("Downloading pristine 16-bit base Gemma 4 E4B model...")
base_model = AutoModelForCausalLM.from_pretrained(
    "unsloth/gemma-4-e4b-it", 
    torch_dtype=torch.float16,
    device_map="cpu" 
)
tokenizer = AutoTokenizer.from_pretrained("unsloth/gemma-4-e4b-it")

# Step 3: Snap your trained CBT adapters onto the base model
print("Applying your trained CBT adapters...")
peft_model = PeftModel.from_pretrained(base_model, adapter_path)

# Step 4: Mathematically fuse them together
print("Fusing weights mathematically (merge_and_unload)...")
fused_model = peft_model.merge_and_unload()

# Step 5: Save the raw files for the compiler
print("Saving fused model to disk...")
fused_model.save_pretrained(hf_folder)
tokenizer.save_pretrained(hf_folder)
print("✅ HuggingFace model successfully saved!")

# Step 6: Setup Llama.cpp safely
print("Setting up Llama.cpp compiler...")
os.system("cd /kaggle/working && rm -rf llama.cpp && git clone https://github.com/ggerganov/llama.cpp")
os.system("pip install -r /kaggle/working/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt")

# Step 7: Compress to GGUF
print("Compressing model into GGUF format (8-bit)...")
convert_cmd = f"python /kaggle/working/llama.cpp/convert_hf_to_gguf.py {hf_folder} --outfile /kaggle/working/sanctuary_cbt_gemma4_e4b_final.gguf --outtype q8_0"
exit_code = os.system(convert_cmd)

if exit_code == 0:
    print("✅ MISSION ACCOMPLISHED. Refresh your Kaggle Output folder and download sanctuary_cbt_gemma4_e4b_final.gguf!")
else:
    print("❌ Conversion failed. Check the Kaggle console logs.")