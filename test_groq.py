import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("API KEY NOT FOUND")
    exit()

client = OpenAI(
    api_key=api_key.strip(),
    base_url="https://api.groq.com/openai/v1",
    timeout=60.0
)

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "Say Hello"
            }
        ]
    )

    print("AI RESPONSE:")
    print(response.choices[0].message.content)

except Exception as e:
    print("ERROR:")
    print(type(e).__name__)
    print(str(e))