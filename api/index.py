from flask import Flask, request, jsonify
from zalo_bot import Update, Bot
from zalo_bot.ext import ApplicationBuilder, CommandHandler

app = Flask(__name__)

# Cấu hình Bot
TOKEN = "YOUR_ZALO_TOKEN_HERE"
bot_app = ApplicationBuilder().token(TOKEN).build()

# Đăng ký các lệnh (Handler)
async def start(update, context):
    await update.message.reply_text("Chào bạn! Bot đã nhận tín hiệu trực tiếp từ Zalo.")

bot_app.add_handler(CommandHandler("start", start))

@app.route('/api/webhook', methods=['POST', 'GET'])
async def v_webhook():
    # 1. Zalo thỉnh thoảng gửi GET để kiểm tra webhook có sống không
    if request.method == 'GET':
        return "Webhook is active", 200

    # 2. Xử lý dữ liệu POST từ Zalo
    try:
        data = request.get_json()
        if data:
            # Chuyển đổi JSON thành Update object và xử lý
            update = Update.de_json(data, bot_app.bot)
            await bot_app.process_update(update)
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 400

# Để Flask chạy được trên Vercel
def handler(event, context):
    return app(event, context)