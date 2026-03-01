import sys, urllib.request, re
try:
    url = sys.argv[1]
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        text = re.sub(r'<script.*?</script>', '', html, flags=re.IGNORECASE|re.DOTALL)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.IGNORECASE|re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        print(re.sub(r'\s+', ' ', text).strip()[:8000])
except Exception as e:
    print(f"Error scraping: {e}")
