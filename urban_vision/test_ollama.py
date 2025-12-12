import requests
import json

resp = requests.post(
    "http://127.0.0.1:11434/api/chat",
    json={
        "model": "qwen3-vl:4b",
        "messages": [
            {
                "role": "user",
                "content": "hello"
            }
        ],
        "stream": False
    },
)

print(resp.status_code)
print(resp.text)
