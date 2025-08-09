import os
import openpyxl
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from datetime import datetime
import threading
import http.server
import socketserver

# === Fake server (keeps Render/Railway alive) ===
def run_fake_server():
    PORT = int(os.environ.get("PORT", 10000))  # Use platform port or fallback to 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Fake server running on port {PORT}")
        httpd.serve_forever()

# Start fake server in background thread (daemon so it won't block main bot)
threading.Thread(target=run_fake_server, daemon=True).start()

# === Bot Token ===
BOT_TOKEN = "7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc"  # Replace with your actual Telegram bot token

# === ChartImg API Key ===
CHARTIMG_API_KEY = "CM0yrQ7JPs7EFsoZg2d0D7nDt7j46f8v34Gr15oT"  # Replace with your actual ChartImg API key

# === Admin Telegram ID ===
ADMIN_USER_ID = 5969585611

# === Load Excel fundamentals once ===
EXCEL_FILE = "fundamentals.xlsx"
stock_data = {}

def load_excel_once():
    global stock_data
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            name = row[0]
            if name:
                stock_data[name.lower()] = dict(zip(headers[1:], row[1:]))
        print(f"✅ Loaded {len(stock_data)} stocks into memory.")
    except Exception as e:
        print(f"❌ Error loading Excel: {e}")

load_excel_once()

# === Calculate score based on fundamentals ===
def calculate_score(data):
    score = 0
    try:
        if data.get("ROCE", 0) > 15: score += 1
        if data.get("ROE", 0) > 15: score += 1
        if 15 < data.get("P/E Ratio", 0) < data.get("Interest Coverage Ratio", 0): score += 1
        if data.get("P/B Ratio", 0) < 1: score += 1
        if data.get("Interest Coverage Ratio", 0) > 3: score += 1
        if data.get("Current Ratio", 0) > 1: score += 1
        if data.get("EPS", 0) > 8: score += 1
        if data.get("Dividend Yield", 0) > 1: score += 1
        if data.get("Promoter Holding", 0) > 50: score += 1
        if data.get("Pledged %", 0) < 10: score += 1
        if data.get("Debt/Equity", 0) < 0.5: score += 1
        if data.get("PEG Ratio", 0) < 1: score += 1
    except Exception as e:
        print(f"⚠️ Error calculating score: {e}")
    return score

# === Get fundamentals string message ===
def get_fundamentals(stock_query):
    for name, data in stock_data.items():
        if stock_query.lower() in name:
            msg = f"📊 {name.title()} Fundamentals:\n"
            for key, value in data.items():
                msg += f"{key}: {value}\n"
            score = calculate_score(data)
            msg += f"\n✅ Total Score (out of 12): {score}"
            return msg.strip()
    return f"❌ '{stock_query.title()}' not found in database."

# === Get chart image bytes from ChartImg API ===
def get_chart(symbol, timeframe):
    tf_map = {
        "1w": "1W",
        "1d": "1D",
        "5min": "5m",
        "1min": "1m",
        "1h": "1h",
        "1y": "1Y"
    }
    if timeframe not in tf_map:
        return None, "❌ Invalid timeframe! Use 1w, 1d, 5min, 1min, 1h, 1y"

    url = "https://api.chartimg.com/v1/chart"
    params = {
        "symbol": symbol.upper(),
        "interval": tf_map[timeframe],
        "apikey": CHARTIMG_API_KEY
    }
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            return r.content, None
        else:
            return None, f"⚠️ Error fetching chart: {r.status_code} {r.text}"
    except Exception as e:
        return None, f"⚠️ Exception fetching chart: {e}"

# === Log user messages to file ===
def log_user_info(update):
    user = update.effective_user
    user_id = user.id
    username = user.username or "NoUsername"
    name = user.first_name or "NoName"
    message = update.message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {name} (@{username}) ID:{user_id} - {message}\n"
    with open("user_logs.txt", "a", encoding="utf-8") as f:
        f.write(log_line)

# === /logs command for admin only ===
async def send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        with open("user_logs.txt", "rb") as f:
            await update.message.reply_document(InputFile(f, filename="user_logs.txt"))
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Log file not found.")

# === Handle user messages ===
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update)
    text = update.message.text.strip().lower()
    words = text.split()

    # Chart request example: "TCS 1w chart"
    if len(words) >= 3 and words[-1] == "chart":
        symbol = words[0]
        timeframe = words[1]
        img_data, error = get_chart(symbol, timeframe)
        if img_data:
            await update.message.reply_photo(img_data, caption=f"📈 {symbol.upper()} {timeframe} Chart")
        else:
            await update.message.reply_text(error)
        return

    # Fundamentals request example: "Reliance fundamental"
    if "fundamental" in text:
        stock_query = next((w for w in words if "fundamental" not in w), None)
        if stock_query:
            msg = get_fundamentals(stock_query)
        else:
            msg = "❌ Type stock name like: Reliance fundamental"
        await update.message.reply_text(msg)
        return

    await update.message.reply_text("❓ Type something like 'TCS fundamental' or 'TCS 1w chart'")

# === Run bot ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("logs", send_logs))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

print("🤖 Bot running...")
app.run_polling()
