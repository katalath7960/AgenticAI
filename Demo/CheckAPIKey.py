import os
import requests

api_key = os.getenv("OPENAI_API_KEY", "")

response = requests.get(
    "https://api.openai.com/v1/models",
    headers={"Authorization": f"Bearer {api_key}"},
)
print("hello")
print(response.status_code)
print(response.text)
