#!/usr/bin/env python3
"""
generate_tree.py — Directory tree markdown generator

Part of radioastronomyio shared utilities
https://github.com/radioastronomyio

Generates TREE_DIRS (directories only) and TREE_ALL (with files) markdown
files for repository documentation. Outputs to scratch/ by default for
review before committing to docs/.

Usage:
    python generate_tree.py                    # Current dir → ./scratch
    python generate_tree.py --root /path/to/repo
    python generate_tree.py --output ./docs   # Override output location
    python generate_tree.py --sizes           # Include file sizes
"""

import argparse
import os
from datetime import datetime

# Directories/files excluded by default — common clutter that obscures structure
DEFAULT_EXCLUDE = {
    '.git', '.vscode', 'node_modules', '__pycache__', '.pytest_cache',
    'dist', 'build', '.env', 'venv', '.venv', 'SBOM', '.idea', '.DS_Store',
    '.ai-sandbox', 'staging', 'scratch'
}


def get_timestamp():
    """Return ISO 8601 timestamp sanitized for filenames (colons → hyphens)."""
    return datetime.now().strftime('%Y-%m-%dT%H-%M-%S')


def get_repo_name(root_path):
    """Extract repository name from root directory path."""
    return os.path.basename(os.path.abspath(root_path))


def should_exclude(name, exclude_set):
    """Check if directory/file should be excluded from tree."""
    return name in exclude_set


def format_size(size_bytes):
    """Format file size in human-readable units (B/KB/MB/GB/TB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:6.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:6.1f} TB"


def build_tree(root_path, exclude_set, include_files=False, show_sizes=False):
    """
    Build tree structure as list of strings with box-drawing characters.
    
    Args:
        root_path: Directory to start from
        exclude_set: Names to skip
        include_files: If True, include files (TREE_ALL); if False, dirs only
        show_sizes: If True, append file sizes in brackets
    
    Returns:
        List of strings, one per tree line
    """
    # AI NOTE: Tree lines use box-drawing chars (├── └── │). Prefix tracking
    # is stateful — each recursion level adds either "│   " (more siblings) or
    # "    " (last sibling). Messing with prefix logic breaks visual alignment.
    
    tree = []
    root_path = os.path.abspath(root_path)
    
    def walk_dir(current_path, prefix="", is_last=True):
        """Recursively walk directory and build tree lines."""
        try:
            entries = sorted(os.listdir(current_path))
        except PermissionError:
            return
        
        # Directories first, then files — consistent visual ordering
        dirs = [e for e in entries if os.path.isdir(os.path.join(current_path, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(current_path, e))]
        
        dirs = [d for d in dirs if not should_exclude(d, exclude_set)]
        files = [f for f in files if not should_exclude(f, exclude_set)]
        
        # Process directories
        for i, dirname in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and (not include_files or not files)
            connector = "└── " if is_last_dir else "├── "
            tree.append(f"{prefix}{connector}{dirname}/")
            
            dir_path = os.path.join(current_path, dirname)
            extension = "    " if is_last_dir else "│   "
            walk_dir(dir_path, prefix + extension, is_last_dir)
        
        # Process files if requested
        if include_files:
            for i, filename in enumerate(files):
                is_last_file = (i == len(files) - 1)
                connector = "└── " if is_last_file else "├── "
                
                if show_sizes:
                    file_path = os.path.join(current_path, filename)
                    try:
                        size = os.path.getsize(file_path)
                        size_str = format_size(size)
                        tree.append(f"{prefix}{connector}{filename} [{size_str}]")
                    except OSError:
                        tree.append(f"{prefix}{connector}{filename}")
                else:
                    tree.append(f"{prefix}{connector}{filename}")
    
    tree.append(f"{os.path.basename(root_path)}/")
    walk_dir(root_path, "", True)
    
    return tree


def write_tree_markdown(root_path, output_dir, repo_name, timestamp, 
                        exclude_set, include_files=False, show_sizes=False):
    """
    Generate and write tree markdown file.
    
    Filename pattern: {repo_name}-TREE_{DIRS|ALL}-{timestamp}.md
    """
    tree_type = "ALL" if include_files else "DIRS"
    filename = f"{repo_name}-TREE_{tree_type}-{timestamp}.md"
    output_path = os.path.join(output_dir, filename)
    
    header = [
        f"# Repository Tree: {repo_name}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Type:** {'Directories and Files' if include_files else 'Directories Only'}  ",
        f"**Root:** `{os.path.abspath(root_path)}`",
        "",
        "```",
    ]
    
    tree = build_tree(root_path, exclude_set, include_files, show_sizes)
    footer = ["```"]
    
    content = "\n".join(header + tree + footer)
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate repository tree documentation in markdown format.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--root',
        default='.',
        help='Root directory to analyze (default: current directory)'
    )
    
    # AI NOTE: Default output is scratch/, not docs/. Trees go to scratch for
    # review before being moved to docs/ or used in READMEs. Changing this
    # default affects the shared utility workflow across repos.
    parser.add_argument(
        '--output',
        default='./scratch',
        help='Output directory for markdown files (default: ./scratch)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=[],
        help='Additional directories/files to exclude (extends default list)'
    )
    
    parser.add_argument(
        '--sizes',
        action='store_true',
        help='Include file sizes in TREE_ALL output'
    )
    
    args = parser.parse_args()
    
    exclude_set = DEFAULT_EXCLUDE.copy()
    exclude_set.update(args.exclude)
    
    repo_name = get_repo_name(args.root)
    timestamp = get_timestamp()
    
    # Always generate both trees — dirs-only for quick overview, all for detail
    dirs_file = write_tree_markdown(
        args.root, args.output, repo_name, timestamp, 
        exclude_set, include_files=False, show_sizes=False
    )
    
    all_file = write_tree_markdown(
        args.root, args.output, repo_name, timestamp,
        exclude_set, include_files=True, show_sizes=args.sizes
    )
    
    print(f"Generated: {dirs_file}")
    print(f"Generated: {all_file}")


if __name__ == '__main__':
    main()
