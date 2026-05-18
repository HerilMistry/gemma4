import os
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from llama_cpp import Llama

def probe_small_model():
    model_path = Path(__file__).resolve().parent.parent / "backend" / "models" / "sanctuary_cbt_final.gguf"
    print("=" * 80)
    print(f"PROBING SMALL MODEL: sanctuary_cbt_final.gguf")
    print(f"Path: {model_path}")
    print(f"Size: {model_path.stat().st_size / (1024 * 1024 * 1024):.2f} GB")
    
    if not model_path.exists():
        print("[FAIL] Model file does not exist!")
        return

    print("Attempting to load model...")
    t0 = time.time()
    try:
        # Load model
        llm = Llama(
            model_path=str(model_path),
            n_ctx=1024,
            n_threads=4,
            verbose=False
        )
        print(f"[OK] Loaded successfully in {time.time() - t0:.2f} seconds.")
    except Exception as e:
        print(f"[FAIL] Failed to load model: {e}")
        return

    # Let's try two prompt formats:
    # 1. Chat completion combining system prompt into user prompt
    print("\n--- Test 1: Chat Completion (System instructions combined into User role) ---")
    messages = [
        {"role": "user", "content": "You are Sanctuary, a supportive, clinical-grade CBT therapist. Respond in 1-2 sentences using CBT principles.\n\nUser concern: I feel so anxious about my exam tomorrow. What should I do?"}
    ]
    t_start = time.time()
    try:
        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            min_p=0.05,
            repeat_penalty=1.1,
        )
        gen_time = time.time() - t_start
        response = output["choices"][0]["message"]["content"].strip()
        usage = output.get("usage", {})
        speed = usage.get("completion_tokens", 0) / gen_time if gen_time > 0 else 0
        
        print("Response:")
        print(response.encode('ascii', errors='replace').decode('ascii'))
        print(f"Speed: {speed:.2f} tokens/second (Gen Time: {gen_time:.2f}s)")
    except Exception as e:
        print(f"[FAIL] Chat completion failed: {e}")

    # 2. Raw Text Completion (using the exact Gemma 2 chat template structure)
    # Gemma Instruct template format:
    # <bos><start_of_turn>user
    # Prompt text<end_of_turn>
    # <start_of_turn>model
    print("\n--- Test 2: Raw Text Completion (Explicit Gemma Instruct template) ---")
    system_instruction = "You are Sanctuary, an advanced Socratic CBT reasoning engine. Help the user deconstruct their thoughts."
    user_input = "I feel so anxious about my exam tomorrow. What should I do?"
    
    # Let's construct a prompt exactly matching how Unsloth / Gemma formats instructions
    prompt = f"<bos><start_of_turn>user\n{system_instruction}\n\nUser input: {user_input}<end_of_turn>\n<start_of_turn>model\n"
    
    t_start = time.time()
    try:
        output = llm(
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["<end_of_turn>", "<eos>"]
        )
        gen_time = time.time() - t_start
        response = output["choices"][0]["text"].strip()
        
        # Calculate tokens/sec
        # We can approximate token count by characters / 4 or look at the response usage
        usage = output.get("usage", {})
        comp_tokens = usage.get("completion_tokens", 0)
        speed = comp_tokens / gen_time if gen_time > 0 else 0
        
        print("Response:")
        print(response.encode('ascii', errors='replace').decode('ascii'))
        print(f"Speed: {speed:.2f} tokens/second (Gen Time: {gen_time:.2f}s)")
    except Exception as e:
        print(f"[FAIL] Raw completion failed: {e}")

if __name__ == "__main__":
    probe_small_model()
