import os
import io
import mailparser
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Đọc các biến môi trường
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

def send_to_telegram(subject, sender, text_content, html_content):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    # 1. Gửi tin nhắn văn bản tóm tắt
    msg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    preview_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
    summary = (
        f"<b>📧 EMAIL MỚI NHẬN</b>\n\n"
        f"<b>👤 Từ:</b> {sender}\n"
        f"<b>📝 Tiêu đề:</b> {subject}\n\n"
        f"<b>📄 Nội dung:</b>\n<i>{preview_text or 'Chỉ có định dạng HTML'}</i>"
    )
    requests.post(msg_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": summary, "parse_mode": "HTML"})

    # 2. Gửi file HTML để xem đầy đủ
    if html_content:
        doc_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        html_file = io.BytesIO(html_content.encode('utf-8'))
        html_file.name = "email_full_view.html"
        requests.post(doc_url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": html_file})

def send_to_webhook(data):
    if not WEBHOOK_URL:
        return
    try:
        # Gửi POST request kèm JSON đến Webhook của bạn
        requests.post(WEBHOOK_URL, json=data, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Webhook: {e}")

@app.route('/api/decode', methods=['POST'])
def handle_email():
    try:
        payload = request.json
        raw_str = payload.get('raw')
        
        if not raw_str:
            return jsonify({"status": "error", "message": "No raw data"}), 400

        # Giải mã chuẩn với mail-parser
        mail = mailparser.parse_from_string(raw_str)
        
        email_data = {
            "from": mail.from_[0][1] if mail.from_ else "Unknown",
            "to": [t[1] for t in mail.to] if mail.to else [],
            "subject": mail.subject or "No Subject",
            "text": mail.text_plain[0] if mail.text_plain else "",
            "html": mail.text_html[0] if mail.text_html else "",
            "date": str(mail.date)
        }

        # Thực hiện đồng thời 2 tác vụ: Gửi Telegram và Webhook
        send_to_telegram(email_data["subject"], email_data["from"], email_data["text"], email_data["html"])
        send_to_webhook(email_data)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
