import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def build_base_url(host: str, port: str, path: str) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"http://{host}:{port}{normalized_path}".rstrip("/")


def http_request(method: str, url: str, data: dict | None = None, timeout: float = 10.0) -> tuple[int, str, dict | None]:
    headers = {"Content-Type": "application/json"}
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(url=url, data=encoded_data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            raw = response.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            return status_code, raw, payload
    except urllib.error.HTTPError as http_err:
        raw = http_err.read().decode("utf-8", errors="replace")
        return http_err.code, raw, None
    except urllib.error.URLError as url_err:
        raise ConnectionError(f"Failed to connect to {url}: {url_err}") from url_err


def list_tools(base_url: str) -> list[str] | None:
    tools_url = f"{base_url}/tools"
    status, raw, payload = http_request("GET", tools_url)
    if status != 200:
        print(f"[warn] GET {tools_url} -> HTTP {status}: {raw[:200]}")
        return None

    # payload could be a list or an object containing tools
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("tools", "available_tools"):
            if key in payload and isinstance(payload[key], list):
                return [str(item) for item in payload[key]]
    return None


def invoke_use_memory_agent(base_url: str, question: str) -> tuple[int, str]:
    url = f"{base_url}/tools/use_memory_agent"
    status, raw, payload = http_request("POST", url, data={"question": question})
    if payload is None:
        return status, raw

    # Try common response shapes
    if isinstance(payload, dict):
        for key in ("result", "data", "reply"):
            if key in payload and isinstance(payload[key], str):
                return status, payload[key]
        # Fallback to pretty JSON dump
        return status, json.dumps(payload, ensure_ascii=False)
    return status, raw


def main() -> int:
    parser = argparse.ArgumentParser(description="Test the MCP HTTP server (FastMCP)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", default="8765", help="Server port (default: 8765)")
    parser.add_argument("--path", default="/mcp-memory-agent", help="Base path (default: /mcp-memory-agent)")
    parser.add_argument("--question", default="I'm happy that today is my birthday", help="Question to send to use_memory_agent")
    args = parser.parse_args()

    base_url = build_base_url(args.host, args.port, args.path)

    print(f"Testing MCP server at: {base_url}")
    # Small delay in case server was just started
    time.sleep(0.25)

    try:
        tools = list_tools(base_url)
        if tools is not None:
            print("Available tools:")
            for t in tools:
                print(f" - {t}")
        else:
            print("[info] Could not list tools. Proceeding to invoke use_memory_agent directly...")

        status, reply = invoke_use_memory_agent(base_url, args.question)
        ok = 200 <= status < 300
        print(f"POST /tools/use_memory_agent -> HTTP {status}")
        print("Response:")
        print(reply)
        return 0 if ok else 2
    except ConnectionError as ce:
        print(f"[error] {ce}")
        print("Hint: Start the server first, e.g.: make mcp-serve")
        return 1


if __name__ == "__main__":
    sys.exit(main())


