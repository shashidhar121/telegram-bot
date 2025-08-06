import threading
import http.server
import socketserver

def run_fake_server():
    PORT = 10000  # Any unused port
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

# Start fake server in background
threading.Thread(target=run_fake_server, daemon=True).start()
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import openpyxl
import os

# Read from Excel
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
        current_ratio = sheet['D2'].value
        eps = sheet['E2'].value
        div_yield = sheet['F2'].value
        promoter = sheet['G2'].value
        pledged = sheet['H2'].value
        debt_eq = sheet['I2'].value
        peg = sheet['J2'].value
        sales = sheet['K2'].value
        op_profit = sheet['L2'].value
        net_profit = sheet['M2'].value

        return (
            f"📊 {stock_name.upper()} Fundamentals:\n"
            f"ROCE: {roce}\n"
            f"ROE: {roe}\n"
            f"P/E Ratio: {pe}\n"
            f"Current Ratio: {current_ratio}\n"
            f"EPS: {eps}\n"
            f"Dividend Yield: {div_yield}\n"
            f"Promoter Holding: {promoter}\n"
            f"Pledged %: {pledged}\n"
            f"Debt/Equity: {debt_eq}\n"
            f"PEG Ratio: {peg}\n"
            f"Sales: {sales}\n"
            f"Operating Profit: {op_profit}\n"
            f"Net Profit: {net_profit}"
        )
    except Exception as e:
        return f"⚠️ Error reading Excel: {str(e)}"

# Respond to messages
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    print(f"Received message: {text}")  # Debug log

    if "fundamental" in text:
        stock = text.split()[0]
        message = get_fundamentals(stock)
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("❓ Type a message like 'TCS fundamental'.")

# Your bot token (replace with your token inside quotes)
BOT_TOKEN = "7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc"

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
print("🤖 Bot is running... Press Ctrl+C to stop.")
app.run_polling()


