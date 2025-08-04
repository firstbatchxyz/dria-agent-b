#!/usr/bin/env python3
"""
Script to remove the problematic token validation check from vllm processor.py
that causes "Token id out of vocabulary" errors.
"""

import os

def remove_vllm_error():
    file_path = ".venv/lib/python3.11/site-packages/vllm/v1/engine/processor.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Skipping...")
        return
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find and remove the problematic lines
    lines_to_remove = []
    for i, line in enumerate(lines):
        if "if max_input_id > tokenizer.max_token_id:" in line:
            lines_to_remove.append(i)
            # Also remove the next line which contains the ValueError
            if i + 1 < len(lines) and "raise ValueError" in lines[i + 1]:
                lines_to_remove.append(i + 1)
            if i + 2 < len(lines) and "is out of vocabulary" in lines[i + 2]:
                lines_to_remove.append(i + 2)
    
    if lines_to_remove:
        print(f"Removing lines {[i+1 for i in lines_to_remove]} from {file_path}")
        # Remove lines in reverse order to maintain correct indices
        for i in reversed(lines_to_remove):
            del lines[i]
        
        # Write the modified content back
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print("Successfully removed problematic token validation check")
    else:
        print("Problematic lines not found or already removed")

if __name__ == "__main__":
    remove_vllm_error() 