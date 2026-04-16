import os
import requests  # 1. Đã thêm import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Thiết lập các biến môi trường
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# URL để chuyển tiếp (Cần có http://... nếu gọi ra ngoài, hoặc gọi trực tiếp hàm nội bộ)
FORWARD_WEBHOOK_URL = os.environ.get("FORWARD_WEBHOOK_URL", "http://127.0.0.1:5000/api/sendtelegram")

@app.route('/api/email', methods=['POST'])
def handle_incoming_email():
    # 1. Nhận dữ liệu từ Webhook
    payload = request.get_json()
    
    # Kiểm tra payload hợp lệ từ Resend
    if not payload or payload.get('type') != 'email.received':
        return jsonify({"status": "ignored", "reason": "Not an email.received event"}), 200

    # 2. Trích xuất email_id
    data = payload.get('data', {})
    email_id = data.get('email_id')
    
    if not email_id:
        return jsonify({"error": "Missing email_id"}), 400

    try:
        # 3. Gọi API Resend để lấy chi tiết nội dung email
        # Lưu ý: Endpoint cho Inbound là /emails/receiving/
        resend_res = requests.get(
            f"https://api.resend.com/emails/receiving/{email_id}", 
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"}
        )
        resend_res.raise_for_status() 
        email_content = resend_res.json()

        # 4. Chuẩn bị dữ liệu để chuyển tiếp
        payload_to_forward = {
            "subject": email_content.get('subject', '(No Subject)'),
            "sender": email_content.get('from'),
            "receiver": email_content.get('to'),
            "body_text": email_content.get('text', ''),
            "body_html": email_content.get('html', ''),
            "email_id": email_id
        }

        # 5. Chuyển tiếp đến endpoint Telegram
        try:
            forward_res = requests.post(FORWARD_WEBHOOK_URL, json=payload_to_forward, timeout=10)
            print(f"✅ Forwarded, Status: {forward_res.status_code}")
        except Exception as webhook_err:
            print(f"⚠️ Forward Error: {str(webhook_err)}")

        return jsonify({
            "status": "success",
            "received_id": email_id,
            "processed": True
        }), 200

    except Exception as e:
        print(f"❌ Resend API Error: {str(e)}")
        return jsonify({"error": "Failed to fetch email details"}), 500

@app.route('/api/sendtelegram', methods=['POST'])
def send_to_telegram():
    data = request.get_json()
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"error": "Telegram config missing"}), 500

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Giới hạn độ dài nội dung để tránh lỗi Telegram (max 4096 ký tự)
    body = (data.get('body_text') or "No content")[:1000]
    
    message = (
        f"📧 *New Email Received*\n"
        f"**Subject:** {data.get('subject')}\n"
        f"**From:** {data.get('sender')}\n"
        f"**To:** {data.get('receiver')}\n\n"
        f"**Content:**\n{body}"
    )

    try:
        tg_res = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })
        return jsonify({"status": "sent_to_telegram", "tg_status": tg_res.status_code}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)