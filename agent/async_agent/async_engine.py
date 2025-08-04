import asyncio
from typing import Optional, Tuple, Dict

from agent.engine import execute_sandboxed_code as sync_execute_sandboxed_code
from agent.settings import SANDBOX_TIMEOUT


async def execute_sandboxed_code(
    code: str,
    timeout: int = SANDBOX_TIMEOUT,
    allow_installs: bool = False,
    requirements_path: str = None,
    allowed_path: str = None,
    blacklist: list = None,
    available_functions: dict = None,
    import_module: str = None,
    log: bool = False,
) -> Tuple[Optional[Dict], str]:
    """
    Async wrapper for executing Python code in a sandboxed subprocess.

    This wraps the synchronous execute_sandboxed_code function to work with async/await.
    Since the underlying implementation uses multiprocessing (which is already non-blocking),
    we run it in a thread executor to avoid blocking the event loop.

    Parameters:
        code (str): The Python code to execute.
        timeout (int): Maximum execution time in seconds for the sandboxed code.
        allow_installs (bool): If True, allow installing missing packages via pip.
        requirements_path (str): Path to a requirements.txt file to install before execution.
        allowed_path (str): Directory path that the code is allowed to access for file I/O.
        blacklist (list): List of names (builtins or module attributes) that are disallowed.
        available_functions (dict): Dictionary of functions to make available in the sandbox.
        import_module (str): Name of a Python module to import and make available.
        log (bool): Whether to enable logging.

    Returns:
        (dict, str): A tuple containing the dictionary of local variables and error message.
    """
    # Run the synchronous function in a thread executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default executor
        sync_execute_sandboxed_code,
        code,
        timeout,
        allow_installs,
        requirements_path,
        allowed_path,
        blacklist,
        available_functions,
        import_module,
        log,
    )
    return result
