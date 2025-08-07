import openpyxl
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# === Optional: Fake server (safe) ===
import threading
import http.server
import socketserver

def run_fake_server():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# === Bot Token ===
BOT_TOKEN = "7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc"  # Replace with your real token

# === Your Telegram ID (Admin only) ===
ADMIN_USER_ID = 5969585611  # 🔁 Replace with your actual Telegram ID

# === Load Excel Once ===
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
        print(f"❌ Error loading Excel: {str(e)}")

load_excel_once()

# === Score Rules ===
def calculate_score(data):
    score = 0
    try:
        if data["ROCE"] > 15: score += 1
        if data["ROE"] > 15: score += 1
        if data["P/E Ratio"] > 15 and data["P/E Ratio"] < data["Interest Coverage Ratio"]: score += 1
        if data["P/B Ratio"] < 1: score += 1
        if data["Interest Coverage Ratio"] > 3: score += 1
        if data["Current Ratio"] > 1: score += 1
        if data["EPS"] > 8: score += 1
        if data["Dividend Yield"] > 1: score += 1
        if data["Promoter Holding"] > 50: score += 1
        if data["Pledged %"] < 10: score += 1
        if data["Debt/Equity"] < 0.5: score += 1
        if data["PEG Ratio"] < 1: score += 1
    except Exception as e:
        print(f"⚠️ Error calculating score: {e}")
    return score

# === Fundamentals Fetching ===
def get_fundamentals(stock_query):
    for name, data in stock_data.items():
        if stock_query.lower() in name:
            msg = f"📊 {name.title()} Fundamentals:\n"
            for key, value in data.items():
                msg += f"{key}: {value}\n"
            score = calculate_score(data)
            msg += f"\n✅ Total Score (out of 12): {score}"
            return msg.strip()
    return f"❌ '{stock_query.title()}' not found in database. Please check the stock name."

# === Log User Info ===
from datetime import datetime

def log_user_info(update):
    user = update.effective_user
    user_id = user.id
    username = user.username or "NoUsername"
    name = user.first_name or "NoName"
    message = update.message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {name} (@{username}) ID:{user_id} - {message}\n"

    try:
        with open("user_logs.txt", "a") as f:
            f.write(log_line)
    except Exception as e:
        print(f"❌ Error writing user log: {e}")

# === /logs Command (Admin only) ===
async def send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ You are not authorized to access logs.")
        return

    try:
        with open("user_logs.txt", "rb") as f:
            await update.message.reply_document(InputFile(f, filename="user_logs.txt"))
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Log file not found.")

# === Respond to User Messages ===
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update)

    text = update.message.text.strip()
    print(f"User: {text}")
    if "fundamental" in text.lower():
        words = text.split()
        stock_query = next((w for w in words if "fundamental" not in w.lower()), None)
        if stock_query:
            msg = get_fundamentals(stock_query)
        else:
            msg = "❌ Please type stock name like: Reliance fundamental"
    else:
        msg = "❓ Type something like 'TCS fundamental'"
    print(f"Bot: {msg}")
    await update.message.reply_text(msg)

# === Run the Bot ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("logs", send_logs))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

print("🤖 Bot running... Press Ctrl+C to stop.")
app.run_polling()
