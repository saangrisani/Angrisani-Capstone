import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_openai_response(message):
    response = openai.ChatCompletion.create(
        model ="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )
    return response ['choices'][0]['message']['content']
    