import openpyxl
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# === Optional: Fake server (safe) ===
import threading
import http.server
import socketserver

def run_fake_server():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

# Start fake server in background (for Railway or free host)
threading.Thread(target=run_fake_server, daemon=True).start()

# === Bot Token ===
BOT_TOKEN = "7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc"  # Replace with your real token

# === Load Excel Once ===
EXCEL_FILE = "fundamentals.xlsx"
stock_data = {}  # Dictionary to store data

def load_excel_once():
    global stock_data
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]  # First row as header
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

# === Get Fundamentals + Score ===
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

# === Handle Messages ===
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
print("🤖 Bot running... Press Ctrl+C to stop.")
app.run_polling()
