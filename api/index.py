import os
import io
import mailparser
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Đọc các biến môi trường
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

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

        send_to_webhook(email_data)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
