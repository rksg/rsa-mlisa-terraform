#!/usr/bin/env python3
"""
Apply Kubernetes resources with string replacements
"""

import argparse
import os
import sys
import tempfile
import subprocess
import json
import re


def log(message, level="INFO"):
    """Simple logging"""
    colors = {"INFO": "\033[0;34m", "SUCCESS": "\033[0;32m", "WARNING": "\033[1;33m", "ERROR": "\033[0;31m"}
    print(f"{colors.get(level, '')}[{level}]\033[0m {message}")


def check_dependencies():
    """Check if kubectl is available"""
    if not os.system("which kubectl > /dev/null 2>&1") == 0:
        log("kubectl not found. Install from: https://kubernetes.io/docs/tasks/tools/", "ERROR")
        sys.exit(1)


def clean_yaml(content):
    """Remove trailing % characters and ensure proper newline"""
    content = re.sub(r'%$', '', content, flags=re.MULTILINE)
    return content if content.endswith('\n') else content + '\n'


def apply_replacements(content, replacementsJson):
    """Apply string replacements to content"""
    for key,value in replacementsJson.items():
        if key and value:
            content = content.replace('||' + key + '||', value)
    return content


def apply_to_k8s(file_path, context=None, dry_run=False):
    """Apply resources to Kubernetes"""
    cmd = ['kubectl', 'apply', '-f', file_path]
    if context:
        cmd.extend(['--context', context])
    if dry_run:
        cmd.append('--dry-run=client')
        log("DRY RUN MODE - No changes will be applied", "WARNING")
    
    log(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log("Resources applied successfully", "SUCCESS")
        if result.stdout:
            print(result.stdout)
    else:
        log(f"Failed to apply resources: {result.stderr}", "ERROR")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Apply Kubernetes resources with replacements")
    parser.add_argument('-f', '--file', required=True, help='Resources YAML file')
    parser.add_argument('-r', '--replacements', required=True, help='Replacements JSON string')
    parser.add_argument('-c', '--context', help='Kubernetes context')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    # Validate resources file exists
    if not os.path.isfile(args.file):
        log(f"Resources file not found: {args.file}", "ERROR")
        sys.exit(1)
    
    # Validate JSON string format
    try:
        replacementJson = json.loads(args.replacements)
    except json.JSONDecodeError as e:
        log(f"Invalid JSON format in replacements: {e}", "ERROR")
        sys.exit(1)
    
    check_dependencies()
    
    # Read and clean resources file
    with open(args.file, 'r') as f:
        content = f.read()
    content = clean_yaml(content)
    
    # Load and apply replacements
    content = apply_replacements(content, replacementJson)
    
    # Write to temporary file and apply
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        print(content)
        #apply_to_k8s(tmp_path, args.context, args.dry_run)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
