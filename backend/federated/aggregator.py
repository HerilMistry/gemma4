"""
Sanctuary 3.0 — Federated Aggregator
Aggregates LoRA weights from multiple clients using FedAvg.
"""

import os
import torch
from peft import PeftModel, LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

def federated_averaging(lora_paths: list[str], output_path: str):
    """
    Merges multiple LoRA state_dicts by averaging their weights.
    """
    if not lora_paths:
        return
        
    avg_state_dict = None
    num_clients = len(lora_paths)
    
    for path in lora_paths:
        # Load state dict (adapter_model.bin)
        state_dict = torch.load(os.path.join(path, "adapter_model.bin"))
        
        if avg_state_dict is None:
            avg_state_dict = state_dict
        else:
            for key in avg_state_dict.keys():
                avg_state_dict[key] += state_dict[key]
                
    # Average the weights
    for key in avg_state_dict.keys():
        avg_state_dict[key] = avg_state_dict[key] / num_clients
        
    # Save the averaged weights
    os.makedirs(output_path, exist_ok=True)
    torch.save(avg_state_dict, os.path.join(output_path, "adapter_model.bin"))
    
    # Copy config from one of the clients
    import shutil
    shutil.copy(os.path.join(lora_paths[0], "adapter_config.json"), 
                os.path.join(output_path, "adapter_config.json"))
    
    print(f"Federated Averaging complete. Merged {num_clients} clients into {output_path}")

if __name__ == "__main__":
    # Example usage
    # federated_averaging(["client1_lora", "client2_lora"], "global_lora_v1")
    pass
