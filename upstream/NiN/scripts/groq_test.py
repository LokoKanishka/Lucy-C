import requests, sys, os
from dotenv import load_dotenv

load_dotenv('/home/lucy-ubuntu/Escritorio/NIN/.env')
api_key = os.getenv("GROQ_API_KEY")

def ask_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "Hola"
    print(ask_groq(p))
