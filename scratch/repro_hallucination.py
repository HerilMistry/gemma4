import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from llm_engine import generate_response
from server import _build_prompt
from core.constants import SYSTEM_INSTRUCTION, FEW_SHOT_EXAMPLES

def test_hallucination():
    text = "i am not feeling well today because i got injury today"
    clinical_context = ""
    typing_features = {}
    route = "lightweight_local"
    reframing_instructions = "Help the user explore their thoughts with empathy and open-ended questions."
    history = []
    
    prompt = _build_prompt(text, clinical_context, typing_features, route, reframing_instructions, history)
    print("--- PROMPT ---")
    print(prompt)
    print("--------------")
    
    response = generate_response(prompt)
    print("\n--- RESPONSE ---")
    print(response)
    print("----------------")

if __name__ == "__main__":
    test_hallucination()
