import os
import resend
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Thiết lập API Key (Lấy từ https://resend.com/api-keys)
resend.api_key = os.environ.get("RESEND_API_KEY")

@app.route('/api/email', methods=['POST'])
def handle_incoming_email():
    # 1. Nhận dữ liệu từ Webhook
    payload = request.get_json()
    
    if not payload or payload.get('type') != 'email.received':
        return jsonify({"status": "ignored", "reason": "Not an email.received event"}), 200

    # 2. Trích xuất email_id từ object 'data'
    data = payload.get('data', {})
    email_id = data.get('email_id')
    
    if not email_id:
        return jsonify({"error": "Missing email_id"}), 400

    try:
        # 3. Gọi API Resend để lấy chi tiết nội dung email
        # Hàm này sẽ trả về đối tượng chứa 'html', 'text', 'subject', 'from', v.v.
        email_content = resend.Emails.Receiving.get(email_id="37e4414c-5e25-4dbc-a071-43552a4bd53b")

        # 4. Gửi nội dung email đến Webhook khác để xử lý
        subject = email_content.get('subject')
        sender = email_content.get('from')
        receiver = email_content.get('to')
        body_text = email_content.get('text')
        body_html = email_content.get('html')

        webhook_url = os.environ.get("FORWARD_WEBHOOK_URL", "https://your-other-webhook.com/endpoint")
        payload_to_forward = {
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "body_text": body_text,
            "body_html": body_html,
            "email_id": email_id
        }

        try:
            response = requests.post(webhook_url, json=payload_to_forward, timeout=10)
            print(f"✅ Đã chuyển tiếp đến webhook khác, HTTP Status: {response.status_code}")
        except Exception as webhook_err:
            print(f"⚠️ Lỗi khi chuyển tiếp đến webhook khác: {str(webhook_err)}")

        return jsonify({
            "status": "success",
            "received_id": email_id,
            "processed": True
        }), 200

    except Exception as e:
        print(f"❌ Lỗi khi truy vấn chi tiết email: {str(e)}")
        return jsonify({"error": "Failed to fetch email details"}), 500

if __name__ == '__main__':
    # Chạy local để test
    app.run(port=5000, debug=True)