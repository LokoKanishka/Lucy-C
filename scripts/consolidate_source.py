import os

def collect_source_code(root_dir, output_file):
    exclude_dirs = {'.git', 'venv', '.venv', '__pycache__', '.mypy_cache', '.pytest_cache', 'node_modules'}
    exclude_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc', '.pdf', '.bin', '.exe', '.dll', '.so', '.dylib'}
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(root_dir):
            # Filtering directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_extensions):
                    continue
                
                # We only want source code and config
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                
                # Skip the output file itself
                if file == os.path.basename(output_file):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        
                    outfile.write("=" * 80 + "\n")
                    outfile.write(f"FILE: {rel_path}\n")
                    outfile.write("=" * 80 + "\n\n")
                    outfile.write(content)
                    outfile.write("\n\n")
                except Exception as e:
                    print(f"Skipping {rel_path}: {e}")

if __name__ == "__main__":
    project_root = "/home/lucy-ubuntu/Lucy-C"
    output_path = "/home/lucy-ubuntu/Lucy-C/lucy_c_full_source.txt"
    collect_source_code(project_root, output_path)
    print(f"Project source consolidated to: {output_path}")
