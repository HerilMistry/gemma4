import os
import time
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import config, etc.
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from llama_cpp import Llama

def probe_model(model_name: str):
    model_path = Path(__file__).resolve().parent.parent / "backend" / "models" / model_name
    print("=" * 80)
    print(f"PROBING MODEL: {model_name}")
    print(f"Path: {model_path}")
    print(f"Size: {model_path.stat().st_size / (1024 * 1024 * 1024):.2f} GB")
    
    if not model_path.exists():
        print("[FAIL] Model file does not exist!")
        return None

    print("Attempting to load model into llama-cpp...")
    t0 = time.time()
    try:
        # Load with minimal context and CPU threads for safe probing
        llm = Llama(
            model_path=str(model_path),
            n_ctx=512,
            n_threads=4,
            verbose=False
        )
        load_time = time.time() - t0
        print(f"[OK] Loaded successfully in {load_time:.2f} seconds.")
    except Exception as e:
        print(f"[FAIL] Failed to load model: {e}")
        return None

    # Run a test generation
    prompt = "I feel so anxious about my exam tomorrow. What should I do?"
    messages = [
        {"role": "system", "content": "You are a supportive, clinical-grade CBT therapist. Respond briefly in 1-2 sentences using CBT principles."},
        {"role": "user", "content": prompt}
    ]
    
    print("\nRunning test generation...")
    t_start_gen = time.time()
    try:
        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            min_p=0.05,
            repeat_penalty=1.1,
        )
        gen_time = time.time() - t_start_gen
        response = output["choices"][0]["message"]["content"].strip()
        usage = output.get("usage", {})
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        speed = completion_tokens / gen_time if gen_time > 0 else 0
        
        print("\n--- Model Output ---")
        try:
            print(response.encode('ascii', errors='replace').decode('ascii'))
        except Exception:
            print("[Could not print response due to encoding]")
        print("--------------------")
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Completion tokens: {completion_tokens}")
        print(f"Generation time: {gen_time:.2f} seconds")
        print(f"Speed: {speed:.2f} tokens/second\n")
        
        return {
            "name": model_name,
            "size_gb": model_path.stat().st_size / (1024 * 1024 * 1024),
            "load_time": load_time,
            "speed": speed,
            "response": response,
            "status": "success"
        }
    except Exception as e:
        print(f"[FAIL] Error during generation: {e}")
        return {
            "name": model_name,
            "size_gb": model_path.stat().st_size / (1024 * 1024 * 1024),
            "load_time": load_time,
            "status": f"generation_error: {e}"
        }

if __name__ == "__main__":
    models = [
        "sanctuary_cbt_final.gguf",
        "sanctuary_cbt_final-q4_k_m.gguf",
        "sanctuary_cbt_final-q8_0.gguf"
    ]
    
    results = []
    for model in models:
        res = probe_model(model)
        if res:
            results.append(res)
            
    print("=" * 80)
    print("SUMMARY OF PROBING:")
    for r in results:
        status_str = r['status']
        if status_str == "success":
            safe_resp = r['response'][:60].encode('ascii', errors='replace').decode('ascii')
            print(f"- {r['name']}: {r['size_gb']:.2f} GB | Speed: {r['speed']:.2f} t/s | Load: {r['load_time']:.2f}s | Response: \"{safe_resp}...\"")
        else:
            print(f"- {r['name']}: {r['size_gb']:.2f} GB | Status: {status_str}")
    print("=" * 80)
