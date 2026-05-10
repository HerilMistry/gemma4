"""
Sanctuary 3.0 — Federated Client Sync
Orchestrates the local training and weight export for federated learning.
"""

import os
import logging
from training.dpo_trainer_unsloth import train_dpo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYNC_DIR = "federated_sync"

def sync_local_update():
    """
    1. Extracts data from Vault.
    2. Runs DPO fine-tuning (LoRA).
    3. Prepares weights for 'upload' to aggregator.
    """
    logger.info("Starting local sync process...")
    
    # Ensure sync dir exists
    os.makedirs(SYNC_DIR, exist_ok=True)
    
    try:
        # Run the training (exported LoRA weights to lora_updates/local_update)
        train_dpo()
        
        # In a real FL system, we would now upload these to the aggregator.
        # For this prototype, we'll just move them to the sync directory.
        import shutil
        shutil.copytree("lora_updates/local_update", 
                        os.path.join(SYNC_DIR, "latest_update"), 
                        dirs_exist_ok=True)
        
        logger.info("✅ Local update synced successfully to %s", SYNC_DIR)
        
    except Exception as e:
        logger.error("❌ Sync failed: %s", e)

if __name__ == "__main__":
    sync_local_update()
