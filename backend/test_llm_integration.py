import time
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from llm_engine import get_inference_orchestrator
from core.constants import SYSTEM_INSTRUCTION

def run_integration_tests():
    print("=" * 80)
    print("SANCTUARY 3.2 — LLM INTEGRATION & PERFORMANCE BENCHMARK")
    print("=" * 80)
    
    orchestrator = get_inference_orchestrator()
    
    print("Subtask 1: Pre-loading model...")
    t0 = time.time()
    orchestrator._ensure_model_loaded()
    load_time = time.time() - t0
    print(f"[OK] Model loaded in {load_time:.2f} seconds.")
    print(f"Active Model: {orchestrator._model_path.name}")
    print("-" * 80)
    
    # Test messages
    test_messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": "I should have worked harder today. I'm such a lazy failure and I will never succeed."}
    ]
    
    # Test Case 1: Synchronous Generation & Formatting Cleanliness
    print("Test Case 1: Synchronous Response Generation")
    t_start = time.time()
    response = orchestrator.generate(test_messages, max_tokens=150)
    gen_time = time.time() - t_start
    
    print("\n--- Synchronous Therapist Response ---")
    print(response)
    print("--------------------------------------")
    
    # Validation checks
    assert "Detected Distortion:" not in response, "CRITICAL ERROR: 'Detected Distortion:' header was leaked to the user!"
    assert "Sanctuary Response:" not in response, "CRITICAL ERROR: 'Sanctuary Response:' header was leaked to the user!"
    print("[OK] Structural reasoning headers stripped successfully from synchronous response.")
    print(f"Generation Time: {gen_time:.2f} seconds.")
    print("-" * 80)
    
    # Test Case 2: Streaming Generation & Token Filtering Resiliency
    print("Test Case 2: Streaming Response Generation & Buffer Filtering")
    t_stream_start = time.time()
    
    stream = orchestrator.generate_stream(test_messages, max_tokens=150)
    
    first_token_time = None
    streamed_tokens = []
    
    print("\n--- Real-Time Filtered Token Stream ---")
    for token in stream:
        if first_token_time is None:
            first_token_time = time.time() - t_stream_start
            print(f"[TTFT: {first_token_time:.2f}s] ", end="", flush=True)
        
        # Replace non-ASCII chars for Windows stdout printing safety
        safe_token = token.encode('ascii', errors='replace').decode('ascii')
        print(safe_token, end="", flush=True)
        streamed_tokens.append(token)
    print("\n----------------------------------------")
    
    stream_time = time.time() - t_stream_start
    final_stream_text = "".join(streamed_tokens).strip()
    
    assert "Detected Distortion:" not in final_stream_text, "CRITICAL ERROR: 'Detected Distortion:' leaked during streaming!"
    assert "Sanctuary Response:" not in final_stream_text, "CRITICAL ERROR: 'Sanctuary Response:' leaked during streaming!"
    
    token_count = len(streamed_tokens)
    speed = token_count / stream_time if stream_time > 0 else 0
    
    print("[OK] Structural reasoning headers stripped successfully from token stream.")
    print(f"Total Stream Time: {stream_time:.2f} seconds.")
    print(f"Generated Tokens: {token_count}")
    print(f"Inference Throughput: {speed:.2f} tokens/second")
    print("=" * 80)
    print("SUCCESS: SYSTEM INTEGRATION SUCCESSFUL: ALL VERIFICATION PROTOCOLS PASSED.")
    print("=" * 80)

if __name__ == "__main__":
    run_integration_tests()
