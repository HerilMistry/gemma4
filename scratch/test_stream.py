import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import llm_engine

os.environ["SANCTUARY_VIDEO_SYNC"] = "True"

messages = [
    {"role": "system", "content": "You are a clinical CBT assistant."},
    {"role": "user", "content": "[Clinical Grounding: none]\nFeeling balanced but want to reflect on my day to maintain my mental grounding."}
]

print("Testing generate_stream...")
try:
    orchestrator = llm_engine.get_inference_orchestrator()
    print("Orchestrator retrieved:", type(orchestrator))
    for token in orchestrator.generate_stream(messages):
        print(token, end="", flush=True)
    print("\nStream completed successfully!")
except Exception as ex:
    import traceback
    print("\n--- ERROR OCCURRED ---")
    traceback.print_exc()
