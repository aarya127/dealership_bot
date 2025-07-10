from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup, Doctype
import re

app = Flask(__name__)

TARGET_URL = "https://www.401dixievolkswagen.ca"
CHATBOT_HTML = """
<div id="chatbot-container"></div>
<script>
  window.chatbotConfig = {
    title: 'Dealership Assistant',
    position: 'right',
    colors: { primary: '#0046ad' },
    suggestions: ['New Volkswagen models', 'Service appointment', 'Financing options']
  }
</script>
<script src="https://cdn.jsdelivr.net/npm/chatbot-lite@latest/public/chatbot-lite.js"></script>
"""

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # Fetch target page
    target = f"{TARGET_URL}/{path}?{request.query_string.decode()}" if path else TARGET_URL
    resp = requests.get(target)
    content_type = resp.headers.get('Content-Type', '')
    
    # Process HTML pages only
    if "text/html" in content_type:
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Fix 1: Preserve original doctype
        original_doctype = next((item for item in soup if isinstance(item, Doctype)), None)
        doctype_str = f"<!DOCTYPE {original_doctype.name}>" if original_doctype else ""
        
        # Fix 2: Handle base URLs
        if soup.find('base') is None and soup.head:
            base_tag = soup.new_tag('base', href=TARGET_URL)
            soup.head.insert(0, base_tag)
        
        # Fix 3: Remove CSP headers
        for meta in soup.find_all('meta', attrs={'http-equiv': re.compile('content-security-policy', re.I)}):
            meta.decompose()
        
        # Fix 4: Inject chatbot at the very end of body
        if soup.body:
            soup.body.append(BeautifulSoup(CHATBOT_HTML, 'html.parser'))
        
        # Fix 5: Preserve original encoding
        charset = soup.meta.get('charset') if soup.meta and soup.meta.get('charset') else 'utf-8'
        
        # Reconstruct HTML
        html_content = f"{doctype_str}\n{str(soup)}"
        return Response(html_content, content_type=content_type)
    
    # Pass through all other assets directly
    return Response(resp.content, content_type=content_type)

if __name__ == "__main__":
    app.run(port=5000, debug=True)