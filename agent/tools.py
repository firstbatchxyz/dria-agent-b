import os
import tempfile
import uuid
import subprocess
from pathlib import Path

from agent.settings import MEMORY_PATH
from agent.utils import check_size_limits, create_memory_if_not_exists

def get_size(file_or_dir_path: str) -> int:
    """
    Get the size of a file or directory.

    Args:
        file_or_dir_path: The path to the file or directory. 
                          If empty string, returns total memory directory size.

    Returns:
        The size of the file or directory in bytes.
    """
    # Handle empty string by returning total memory size
    if not file_or_dir_path or file_or_dir_path == "":
        # Get the current working directory (which should be the memory root)
        cwd = os.getcwd()
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(cwd):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass
        return total_size
    
    # Otherwise check the specific path
    if os.path.isfile(file_or_dir_path):
        return os.path.getsize(file_or_dir_path)
    elif os.path.isdir(file_or_dir_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(file_or_dir_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass
        return total_size
    else:
        raise FileNotFoundError(f"Path not found: {file_or_dir_path}")

def create_file(file_path: str, content: str = "") -> bool:
    """
    Create a new file in the memory with the given content (if any).
    First create a temporary file with the given content, check if 
    the size limits are respected, if so, move the temporary file to 
    the final destination.

    Args:
        file_path: The path to the file.
        content: The content of the file.

    Returns:
        True if the file was created successfully, False otherwise.
    """
    try:
        # Create a unique temporary file name to avoid conflicts
        temp_file_path = f"temp_{uuid.uuid4().hex[:8]}.txt"
        
        with open(temp_file_path, "w") as f:
            f.write(content)
        
        if check_size_limits(temp_file_path):
            # Move the temporary file to the final destination
            with open(file_path, "w") as f:
                f.write(content)
            os.remove(temp_file_path)
            return True
        else:
            os.remove(temp_file_path)
            return False
    except Exception:
        return False
    
def create_dir(dir_path: str) -> bool:
    """
    Create a new directory in the memory.

    Args:
        dir_path: The path to the directory.

    Returns:
        True if the directory was created successfully, False otherwise.
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception:
        return False

def write_to_file(file_path: str, diff: str) -> bool:
    """
    Try to apply a unified git-style diff to `file_path`.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the file being patched.
    diff : str
        Text in standard unified-diff format (what you get from `git diff`).

    Returns
    -------
    bool
        True  – diff applied cleanly.
        False – any problem (syntax errors, context mismatch, no git in PATH …).
    """
    # Guarantee we run in the directory that contains the target file.
    workdir = Path(file_path).expanduser().resolve().parent

    # Create the temp file in the workdir instead of system /tmp
    # This ensures it's within the sandbox's allowed path
    temp_file_path = workdir / f"temp_patch_{uuid.uuid4().hex[:8]}.patch"

    try:
        # Write the diff to the temp file
        with open(temp_file_path, "w") as tmp:
            tmp.write(diff)
        patch_file = str(temp_file_path)

        # 1. Dry-run check ─ will fail (non-zero return-code) on any conflict.
        check = subprocess.run(
            ["git", "apply", "--check", "--unsafe-paths", patch_file],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            # Optional: log or surface check.stderr for callers.
            return False

        # 2. Real apply (no --check).
        apply = subprocess.run(
            ["git", "apply", "--unsafe-paths", patch_file],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        return apply.returncode == 0
    finally:
        # Clean up the temp file
        if os.path.exists(patch_file):
            os.remove(patch_file)
    
def read_file(file_path: str) -> str:
    """
    Read a file in the memory.

    Args:
        file_path: The path to the file.

    Returns:
        The content of the file, or an error message if the file cannot be read.
    """
    try:
        # Ensure the file path is properly resolved
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: {file_path} is not a file"
            
        with open(file_path, "r") as f:
            return f.read()
    except PermissionError:
        return f"Error: Permission denied accessing {file_path}"
    except Exception as e:
        return f"Error: {e}"
    
def list_files(dir_path: str = None) -> list[str]:
    """
    List all files and directories in the memory. Full paths 
    are returned and directories are searched recursively. An
    example of the output is:
    ["dir/a.txt", "dir/b.txt", "dir/subdir/c.txt", "d.txt"]

    Args:
        dir_path: The path to the directory. If None, uses the current working directory.

    Returns:
        A list of files and directories in the memory.
    """
    try:
        # Use current directory if dir_path is None
        if dir_path is None:
            dir_path = os.getcwd()
        
        # Ensure dir_path is absolute for consistent path handling
        dir_path = os.path.abspath(dir_path)
        
        # Check if the directory exists
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return [f"Error: Directory {dir_path} does not exist or is not a directory"]
            
        result_files = []
        for root, _, files_list in os.walk(dir_path):
            for file in files_list:
                full_path = os.path.join(root, file)
                # Make the path relative to the memory directory (dir_path)
                try:
                    rel_path = os.path.relpath(full_path, dir_path)
                    result_files.append(rel_path)
                except ValueError:
                    # If paths are on different drives on Windows, use absolute path
                    result_files.append(full_path)
        return result_files
    except Exception as e:
        return [f"Error: {e}"]
    
def delete_file(file_path: str) -> bool:
    """
    Delete a file in the memory.

    Args:
        file_path: The path to the file.

    Returns:
        True if the file was deleted successfully, False otherwise.
    """
    try:
        os.remove(file_path)
        return True
    except Exception:
        return False
    
def go_to_link(link_string: str) -> str:
    """
    Go to a link in the memory and return the content of the note Y. A link in a note X to a note Y, with the
    path path/to/note/Y.md, is structured like this:
    [[path/to/note/Y]]

    Args:
        link_string: The link to go to.

    Returns:
        The content of the note Y, or an error message if the link cannot be accessed.
    """
    try:
        # Handle Obsidian-style links: [[path/to/note]] -> path/to/note.md
        if link_string.startswith("[[") and link_string.endswith("]]"):
            file_path = link_string[2:-2]  # Remove [[ and ]]
            if not file_path.endswith('.md'):
                file_path += '.md'
        else:
            file_path = link_string
            
        # Ensure the file path is properly resolved
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found"
        
        if not os.path.isfile(file_path):
            return f"Error: {file_path} is not a file"
            
        with open(file_path, "r") as f:
            return f.read()
    except PermissionError:
        return f"Error: Permission denied accessing {link_string}"
    except Exception as e:
        return f"Error: {e}"

def check_if_file_exists(file_path: str) -> bool:
    """
    Check if a file exists in the given filepath.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        True if the file exists and is a file, False otherwise.
    """
    try:
        return os.path.exists(file_path) and os.path.isfile(file_path)
    except (OSError, TypeError, ValueError):
        return False

def check_if_dir_exists(dir_path: str) -> bool:
    """
    Check if a directory exists in the given filepath.
    
    Args:
        dir_path: The path to the directory.
        
    Returns:
        True if the directory exists and is a directory, False otherwise.
    """
    try:
        return os.path.exists(dir_path) and os.path.isdir(dir_path)
    except (OSError, TypeError, ValueError):
        return False