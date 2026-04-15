from flask import Flask, request, jsonify
import email
from email import policy
import requests

app = Flask(__name__)

# Thông tin Telegram (Nên đặt trong Environment Variables trên Vercel)
TELEGRAM_TOKEN = "8731423127:AAHJC_7KTu5YR96b5H6MTRHD_9_1NCTF1AU"
TELEGRAM_CHAT_ID = "8741135917"

def send_to_telegram(data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Định dạng nội dung tin nhắn
    text_preview = data['text'][:500] + "..." if len(data['text']) > 500 else data['text']
    
    message = (
        f"📧 *EMAIL MỚI NHẬN ĐƯỢC*\n\n"
        f"👤 *Từ:* {data['from']}\n"
        f"🎯 *Đến:* {data['to']}\n"
        f"📝 *Tiêu đề:* {data['subject']}\n\n"
        f"📄 *Nội dung văn bản:*\n{text_preview}"
    )
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    return requests.post(url, json=payload)

def decode_mime(raw_str):
    msg = email.message_from_string(raw_str, policy=policy.default)
    content = {"text": "", "html": ""}
    
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition"))
            if "attachment" not in cdisp:
                payload = part.get_payload(decode=True)
                if not payload: continue
                charset = part.get_content_charset() or 'utf-8'
                try:
                    decoded_payload = payload.decode(charset, errors='ignore')
                    if ctype == "text/plain":
                        content["text"] += decoded_payload
                    elif ctype == "text/html":
                        content["html"] += decoded_payload
                except: pass
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            decoded_payload = payload.decode(charset, errors='ignore')
            if msg.get_content_type() == "text/html":
                content["html"] = decoded_payload
            else:
                content["text"] = decoded_payload
            
    return msg, content

@app.route('/api/decode', methods=['POST'])
def handle_email():
    # Nhận data từ Cloudflare Worker
    data = request.json
    raw_str = data.get('raw')
    
    if not raw_str:
        return jsonify({"error": "No raw content"}), 400

    # 1. Giải mã email chuẩn nhất
    msg, content = decode_mime(raw_str)
    
    result = {
        "from": msg['from'],
        "to": msg['to'],
        "subject": msg['subject'],
        "text": content['text'] or "Không có nội dung văn bản",
        "html": content['html']
    }

    # 2. Gửi cho Telegram Bot
    tg_res = send_to_telegram(result)
    
    if tg_res.status_code == 200:
        return jsonify({"status": "success", "sent_to_telegram": True}), 200
    else:
        return jsonify({"status": "error", "tg_response": tg_res.text}), 500
