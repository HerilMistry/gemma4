"""
Sanctuary 3.0 — Federated RL Client Utilities
Extracts preference pairs from the encrypted SecureVault for DPO training.
"""

import logging
import json
from database import SecureVault

logger = logging.getLogger(__name__)

def extract_preference_pairs(min_rating: int = 4, max_rating: int = 2) -> list[dict]:
    """
    Extracts (prompt, chosen, rejected) triplets from the vault.
    
    - 'chosen': High-rated responses (>= min_rating).
    - 'rejected': Low-rated responses (<= max_rating) that have a reframed alternative.
    
    Returns:
        List of dicts: [{"prompt": str, "chosen": str, "rejected": str}, ...]
    """
    vault = SecureVault()
    all_logs = vault.retrieve_and_decrypt()
    all_feedback = vault.retrieve_and_decrypt_feedback()
    
    # Map logs by ID for easy lookup
    logs_map = {log["id"]: log["data"] for log in all_logs}
    
    pairs = []
    
    for fb in all_feedback:
        log_id = fb.get("log_id")
        if log_id not in logs_map:
            continue
            
        log_data = logs_map[log_id]
        prompt = log_data.get("processed_text", "")
        original_response = log_data.get("response", "")
        rating = fb.get("rating")
        feedback_text = fb.get("feedback_text", "")
        
        # Scenario A: The original response was GOOD (Chosen)
        # We need a 'rejected' example. If we don't have one, we might use a baseline.
        # For now, we'll focus on Scenario B.
        
        # Scenario B: The original response was BAD (Rejected)
        # And the feedback contains a "Reframed" (Chosen) version.
        if rating and rating <= max_rating and feedback_text:
            # We assume the feedback_text contains the "Positive Reframing"
            # In a real app, we might have a specific field for this.
            pairs.append({
                "prompt": prompt,
                "chosen": feedback_text,
                "rejected": original_response,
                "source_log_id": log_id
            })
            
    logger.info("Extracted %d preference pairs from vault.", len(pairs))
    return pairs

def prepare_dpo_dataset(pairs: list[dict]):
    """Converts extracted pairs into a format compatible with Hugging Face Datasets."""
    from datasets import Dataset
    
    formatted_data = {
        "prompt": [],
        "chosen": [],
        "rejected": []
    }
    
    for p in pairs:
        # Format prompt according to Gemma's template
        # Note: We strip the 'model' turn start as DPOTrainer adds it usually
        formatted_data["prompt"].append(p["prompt"])
        formatted_data["chosen"].append(p["chosen"])
        formatted_data["rejected"].append(p["rejected"])
        
    return Dataset.from_pandas(Dataset.from_dict(formatted_data).to_pandas())
