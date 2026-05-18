import os
import zipfile
from pathlib import Path

def package_project():
    root_dir = Path(__file__).resolve().parent
    output_zip = root_dir / "sanctuary_edge_native.zip"
    
    print("=" * 60)
    # Windows-friendly character mapping for terminal printing
    print("SANCTUARY 3.2 -- SUBMISSION PACKAGER")
    print("=" * 60)
    print(f"Project root: {root_dir}")
    print(f"Target zip:   {output_zip.name}")
    print("Analyzing and archiving files...")
    
    # Excluded directories
    exclude_dirs = {
        "env",
        "venv",
        ".git",
        "node_modules",
        ".next",
        ".pytest_cache",
        "__pycache__",
        "models",     # Exclude backend/models directory to omit large weights
        "uploads",    # Exclude uploaded files
        "data"        # Exclude local encrypted databases
    }
    
    # Excluded files
    exclude_files = {
        "sanctuary_edge_native.zip",
        "aes_key.bin",
        "sanctuary.db"
    }

    count = 0
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Convert root to Path relative to root_dir
            rel_root = Path(root).relative_to(root_dir)
            
            # Prune directories in-place to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Check if current root path contains any of the excluded directory names
            if any(part in exclude_dirs for part in rel_root.parts):
                continue
                
            for file in files:
                if file in exclude_files or file.endswith('.gguf') or file.endswith('.pyc'):
                    continue
                    
                file_path = Path(root) / file
                arc_name = file_path.relative_to(root_dir)
                
                zipf.write(file_path, arcname=arc_name)
                count += 1
                
    print("-" * 60)
    print(f"[OK] Successfully packaged {count} source files!")
    print(f"[OK] Archive saved: {output_zip}")
    print(f"Size: {output_zip.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 60)
    print("This ZIP file is ready to be uploaded to your hackathon platform.")
    print("=" * 60)

if __name__ == "__main__":
    package_project()
