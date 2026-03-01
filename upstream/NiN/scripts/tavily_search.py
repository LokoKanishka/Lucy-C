import requests, sys, os
from dotenv import load_dotenv

load_dotenv('/home/lucy-ubuntu/Escritorio/NIN/.env')
api_key = os.getenv("TAVILY_API_KEY")

def search(query):
    url = "https://api.tavily.com/search"
    data = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True
    }
    response = requests.post(url, json=data)
    return response.json()

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "latest AI news 2026"
    print(search(q))
