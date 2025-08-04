import difflib


def diff_strings(a: str, b: str, fromfile: str = "a", tofile: str = "b") -> str:
    """
    Return a git‐style unified diff of two multi‐line strings.
    """
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)
    diff = difflib.unified_diff(
        a_lines, b_lines, fromfile=fromfile, tofile=tofile, lineterm=""
    )
    return "".join(line + "\n" for line in diff)


def diff_files(path_a: str, path_b: str) -> str:
    """
    Return a git‐style unified diff of two files.
    """
    with (
        open(path_a, "r", encoding="utf-8") as fa,
        open(path_b, "r", encoding="utf-8") as fb,
    ):
        a = fa.read()
        b = fb.read()
    return diff_strings(a, b, fromfile=path_a, tofile=path_b)
