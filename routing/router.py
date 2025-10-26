import requests
import json

def read_file(path):
    """Read the entire content of a text file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ File not found: {path}")

def query_qwen3(model="qwen3:4b", system_file="SYSTEM_PROMPT", user_file="USER_PROMPT"):
    """
    Query the local Qwen3-4B (Dense) model via Ollama API.
    Reads system and user prompts from text files.
    """
    system_prompt = read_file(system_file)
    user_prompt = read_file(user_file)

    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code} - {response.text}")

    data = response.json()
    return data.get("message", {}).get("content", "")


if __name__ == "__main__":
    print("🚀 Querying Qwen3-4B (Dense) via Ollama...\n")
    answer = query_qwen3()
    print("🧩 Qwen3-4B response:\n")
    print(answer)
