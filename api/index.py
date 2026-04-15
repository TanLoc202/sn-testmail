from flask import Flask, request, jsonify
import email
from email import policy
import requests

app = Flask(__name__)

# Thông tin Telegram (Nên đặt trong Environment Variables trên Vercel)
TELEGRAM_TOKEN = "8731423127:AAHJC_7KTu5YR96b5H6MTRHD_9_1NCTF1AU"
TELEGRAM_CHAT_ID = "8741135917"

def decode_mime(raw_str):
    msg = email.message_from_string(raw_str, policy=policy.default)
    content = {"text": "", "html": ""}
    
    for part in msg.walk():
        ctype = part.get_content_type()
        cdisp = str(part.get("Content-Disposition"))
        
        if "attachment" in cdisp:
            continue
            
        payload = part.get_payload(decode=True)
        if not payload: continue
        
        charset = part.get_content_charset() or 'utf-8'
        try:
            decoded = payload.decode(charset, errors='ignore')
            if ctype == "text/plain":
                content["text"] += decoded
            elif ctype == "text/html":
                content["html"] += decoded
        except: pass
            
    return msg, content

def send_to_telegram(data):
    # 1. Gửi tin nhắn văn bản trước
    msg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    summary = (
        f"<b>📧 EMAIL MỚI</b>\n"
        f"<b>👤 Từ:</b> {data['from']}\n"
        f"<b>📝 Tiêu đề:</b> {data['subject']}\n"
        f"<b>📄 Bản xem trước:</b>\n{data['text'][:300]}..."
    )
    requests.post(msg_url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": summary,
        "parse_mode": "HTML"
    })

    # 2. Nếu có HTML, gửi nó dưới dạng file đính kèm để xem đầy đủ
    if data['html']:
        doc_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        # Tạo file ảo trong bộ nhớ
        html_file = io.BytesIO(data['html'].encode('utf-8'))
        html_file.name = "view_email.html"
        
        requests.post(doc_url, 
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"document": html_file}
        )

@app.route('/api/decode', methods=['POST'])
def handle_email():
    payload = request.json
    raw_str = payload.get('raw')
    
    if not raw_str:
        return jsonify({"error": "No data"}), 400

    msg, content = decode_mime(raw_str)
    
    email_data = {
        "from": str(msg['from']),
        "to": str(msg['to']),
        "subject": str(msg['subject']),
        "text": content['text'],
        "html": content['html']
    }

    send_to_telegram(email_data)
    return jsonify({"status": "sent"}), 200
