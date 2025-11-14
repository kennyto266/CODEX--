#!/usr/bin/env python3
"""
Large File Splitter
Split large Python files (>100KB) into smaller, manageable modules
"""

import os
import re
from pathlib import Path

def split_file_by_classes(filename, output_dir):
    """Split file by class/function definitions"""
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find classes and top-level functions
    sections = []
    current_section = []
    current_name = "module"
    
    for line in content.split('\n'):
        # Class definition
        if re.match(r'^\s*class\s+\w+', line):
            if current_section:
                sections.append((current_name, '\n'.join(current_section)))
            current_section = [line]
            current_name = re.search(r'class\s+(\w+)', line).group(1).lower()
        # Top-level function
        elif re.match(r'^\s*def\s+\w+', line) and not current_section:
            current_section = [line]
            current_name = re.search(r'def\s+(\w+)', line).group(1).lower()
        else:
            if current_section is not None:
                current_section.append(line)
    
    if current_section:
        sections.append((current_name, '\n'.join(current_section)))
    
    # Write split files
    os.makedirs(output_dir, exist_ok=True)
    base_name = Path(filename).stem
    
    for i, (name, section_content) in enumerate(sections):
        output_file = os.path.join(output_dir, f"{base_name}_{name}.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(section_content)
        print(f"Created: {output_file}")
    
    return len(sections)

def create_main_file(original_file, output_dir, module_names):
    """Create a new main file that imports all modules"""
    base_name = Path(original_file).stem
    main_file = os.path.join(output_dir, f"{base_name}.py")
    
    # Read original to get imports and non-class code
    with open(original_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract imports at the top
    imports = []
    for line in content.split('\n'):
        if line.strip().startswith(('import ', 'from ')):
            imports.append(line)
        elif line.strip() and not line.strip().startswith('#'):
            break
    
    # Create main file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(imports) + '\n\n')
        
        for module in module_names:
            f.write(f"from .{base_name}_{module} import *\n")
    
    print(f"Created: {main_file}")
    return main_file

def main():
    large_files = [
        "complete_project_system.py",
    ]
    
    print("=" * 70)
    print("LARGE FILE SPLITTER")
    print("=" * 70)
    
    for file in large_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"\n[1] Processing: {file}")
            print(f"    Size: {size/1024:.1f} KB")
            
            output_dir = f"split_{Path(file).stem}"
            modules = split_file_by_classes(file, output_dir)
            
            print(f"    Split into {modules} modules")
        else:
            print(f"\n[1] File not found: {file}")
    
    print("\n" + "=" * 70)
    print("FILE SPLITTING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
