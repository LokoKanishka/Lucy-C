import requests, sys, os, json
from dotenv import load_dotenv

load_dotenv('/home/lucy-ubuntu/Escritorio/NIN/.env')
api_key = os.getenv("RESEND_API_KEY")

def send_email(to_email, subject, html_content):
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Resend requires a verified domain to send from custom addresses.
    # While testing, 'onboarding@resend.dev' allows sending only to the registered email.
    data = {
        "from": "Acme <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    response = requests.post(url, headers=headers, json=data)
    try:
        return response.json()
    except Exception:
        return {"error": "Invalid response", "raw": response.text}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Uso: python3 resend_mailer.py <to_email> <subject> <html_content>"}))
        sys.exit(1)
    
    to = sys.argv[1]
    subj = sys.argv[2]
    html = sys.argv[3]
    
    result = send_email(to, subj, html)
    print(json.dumps(result))
