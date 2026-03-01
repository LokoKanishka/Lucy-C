import requests, sys, os, json
from dotenv import load_dotenv

load_dotenv('/home/lucy-ubuntu/Escritorio/NIN/.env')
api_key = os.getenv("HF_API_KEY")

def ask_hf(model_id, payload):
    url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except:
        return {"error": "Invalid response", "raw": response.text}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Uso: python3 hf_inference.py <model_id> <payload_json_string>"}))
        sys.exit(1)
    
    model = sys.argv[1]
    raw_payload = sys.argv[2]
    try:
        payload = json.loads(raw_payload)
    except:
        payload = {"inputs": raw_payload}
        
    result = ask_hf(model, payload)
    print(json.dumps(result))
