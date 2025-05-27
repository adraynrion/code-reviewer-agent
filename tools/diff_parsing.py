"""Diff parsing utilities for the code review agent."""

import logging
from typing import Dict, List, Any
from langfuse_decorators import track_tool

# Configure logger
logger = logging.getLogger(__name__)

def log_info(message: str):
    """Log an info message to the logger."""
    logger.info(message)

def log_error(message: str, exc_info=None):
    """Log an error message to the logger."""
    logger.error(message, exc_info=exc_info)

@track_tool(name="parse_unified_diff", metadata={"component": "diff_parsing"})
def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parse a GitHub-provided unified diff into structured file diffs.

    Args:
        diff_text: The unified diff text from GitHub

    Returns:
        List of parsed file diffs with metadata
    """
    log_info("Starting to parse unified diff")
    log_info(f"Diff text size: {len(diff_text)} characters")

    # Log first 500 chars of diff for debugging
    log_info(f"Diff preview (first 500 chars):\n{diff_text[:500]}...")
    log_info(f"Diff ends with: ...{diff_text[-100:] if len(diff_text) > 100 else diff_text}")

    if not diff_text.strip():
        log_error("Empty diff text received")

    files = []
    current_file = None
    splited_diff_text = diff_text.split('\n')
    file_count = 0

    for line in splited_diff_text:
        # Start of a new file diff
        if line.startswith('diff --git'):
            # Process previous file if exists
            if current_file is not None:
                if 'patch' in current_file and isinstance(current_file['patch'], list):
                    current_file['patch'] = '\n'.join(current_file['patch'])
                files.append(current_file)
                file_count += 1
                log_info(f"Completed processing file {file_count}: {current_file.get('filename', 'unknown')} "
                       f"({current_file.get('status', 'unknown')} - {len(current_file.get('patch', '').splitlines())} lines)")

            # Extract old and new file paths
            parts = line.split()
            old_path = parts[2][2:]  # Skip 'a/'
            new_path = parts[3][2:]  # Skip 'b/'


            # Determine file status
            status = 'modified'
            if old_path == '/dev/null':
                status = 'added'
            elif new_path == '/dev/null':
                status = 'deleted'

            # Determine filename
            filename = old_path
            if new_path != '/dev/null':
                filename = new_path

            # Determine previous filename
            previous_filename = None
            if old_path != '/dev/null':
                previous_filename = old_path

            # Initialize new file
            current_file = {
                'filename': filename,
                'status': status,
                'patch': []
            }
            log_info(f"Starting to process file: {new_path} (status: {status})")

            current_file['previous_filename'] = previous_filename
            current_file['additions'] = 0
            current_file['deletions'] = 0
            current_file['is_binary'] = False

            # Check for binary file indicator in the next 5 lines
            next_lines = splited_diff_text[splited_diff_text.index(line) + 1:splited_diff_text.index(line) + 5]
            for l in next_lines:
                if 'binary' in l.lower():
                    current_file['is_binary'] = True
                    break

        # Parse diff metadata
        elif line.startswith('index ') and current_file:
            # Extract SHAs if available (format: index <base-sha>..<head-sha> <mode>)
            parts = line.split()
            if '..' in parts[1]:
                base_sha, head_sha = parts[1].split('..')[:2]
                current_file['base_sha'] = base_sha
                current_file['head_sha'] = head_sha

        # Parse hunk headers
        elif line.startswith('@@ ') and current_file and not current_file['is_binary']:
            current_file['patch'].append(line)

        # Parse added/removed lines
        elif current_file and not current_file['is_binary']:
            if line.startswith('+') and not line.startswith('+++'):
                current_file['additions'] += 1
                current_file['patch'].append(line)
            elif line.startswith('-') and not line.startswith('---'):
                current_file['deletions'] += 1
                current_file['patch'].append(line)
            elif line.startswith(' '):
                current_file['patch'].append(line)

    # Add the last file if exists
    if current_file is not None:
        if 'patch' in current_file and isinstance(current_file['patch'], list):
            current_file['patch'] = '\n'.join(current_file['patch'])
        files.append(current_file)
        file_count += 1
        log_info(f"Completed processing final file: {current_file.get('filename', 'unknown')} "
               f"({current_file.get('status', 'unknown')} - {len(current_file.get('patch', '').splitlines())} lines)")

    log_info(f"Successfully parsed {file_count} files from diff")
    log_info(f"Total chunks in diff: {len([f for f in files if 'patch' in f])}")

    # Log summary of parsed files
    if files:
        log_info("Parsed files summary:")
        for i, f in enumerate(files, 1):
            log_info(f"  {i}. {f.get('filename', 'unknown')} ({f.get('status', 'unknown')}) - "
                   f"{len(f.get('patch', '').splitlines())} lines")
    else:
        log_info("No files were parsed from the diff")

    return files
