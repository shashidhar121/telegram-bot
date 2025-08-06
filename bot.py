import threading
import http.server
import socketserver
import os
import openpyxl
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Run a fake HTTP server in the background (useful for keeping bot alive on some platforms)
def run_fake_server():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# Read stock fundamentals from Excel
def get_fundamentals(stock_name):
    file_name = f"{stock_name.upper()}.xlsx"
    if not os.path.exists(file_name):
        return "❌ Excel file not found. Please upload it as 'TCS.xlsx', etc."

    try:
        wb = openpyxl.load_workbook(file_name)
        sheet = wb.active

        roce = sheet['A2'].value
        roe = sheet['B2'].value
        pe = sheet['C2'].value
        pb = sheet['D2'].value
        int_coverage = sheet['E2'].value
        current_ratio = sheet['F2'].value
        eps = sheet['G2'].value
        div_yield = sheet['H2'].value
        promoter = sheet['I2'].value
        pledged = sheet['J2'].value
        debt_eq = sheet['K2'].value
        peg = sheet['L2'].value

        return (
            f"📊 {stock_name.upper()} Fundamentals:\n"
            f"ROCE: {roce}\n"
            f"ROE: {roe}\n"
            f"P/E Ratio: {pe}\n"
            f"P/B Ratio: {pb}\n"
            f"Interest Coverage Ratio: {int_coverage}\n"
            f"Current Ratio: {current_ratio}\n"
            f"EPS: {eps}\n"
            f"Dividend Yield: {div_yield}\n"
            f"Promoter Holding: {promoter}\n"
            f"Pledged %: {pledged}\n"
            f"Debt/Equity: {debt_eq}\n"
            f"PEG Ratio: {peg}"
        )
    except Exception as e:
        return f"⚠️ Error reading Excel: {str(e)}"

# Respond to user messages
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    print(f"Received message: {text}")  # Debug log

    if "fundamental" in text:
        words = text.split()
        stock = None
        for word in words:
            if word not in ["fundamental", "fundamentals"]:
                stock = word.upper()
                break
        if stock:
            message = get_fundamentals(stock)
        else:
            message = "❌ Couldn't detect stock name. Try 'TCS fundamental'."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("❓ Type a message like 'TCS fundamental'.")

# Replace with your actual Telegram bot token
BOT_TOKEN = "7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc"

# Set up and run the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
print("🤖 Bot is running... Press Ctrl+C to stop.")
app.run_polling()
