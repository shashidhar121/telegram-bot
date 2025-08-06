import threading
import http.server
import socketserver
import os
import openpyxl
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Run a fake server (only if needed for hosting platforms)
def run_fake_server():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# Load Excel once (global variable)
EXCEL_FILE = "fundamentals.xlsx"

# Read fundamentals for a given stock name
def get_fundamentals(stock_query):
    if not os.path.exists(EXCEL_FILE):
        return f"❌ Excel file '{EXCEL_FILE}' not found. Please upload it."

    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active

        headers = [cell.value for cell in sheet[1]]  # First row headers
        for row in sheet.iter_rows(min_row=2, values_only=True):
            stock_name = row[0]
            if stock_name and stock_query.lower() in stock_name.lower():
                # Prepare response
                message = f"📊 {stock_name} Fundamentals:\n"
                for i in range(1, len(headers)):
                    message += f"{headers[i]}: {row[i]}\n"
                return message.strip()
        return f"❌ Stock '{stock_query}' not found in Excel."
    except Exception as e:
        return f"⚠️ Error reading Excel: {str(e)}"

# Respond to user messages
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    print(f"Received: {text}")

    if "fundamental" in text.lower():
        words = text.split()
        stock_query = None
        for word in words:
            if "fundamental" not in word.lower():
                stock_query = word
                break
        if stock_query:
            message = get_fundamentals(stock_query)
        else:
            message = "❌ Please specify stock name. Example: Reliance fundamental"
    else:
        message = "❓ Type a message like 'TCS fundamental' or 'Reliance fundamental'."

    await update.message.reply_text(message)

# Your Telegram bot token
BOT_TOKEN = "7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc"

# Set up and run the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
print("🤖 Bot is running... Press Ctrl+C to stop.")
app.run_polling()
