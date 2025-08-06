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

        # Correct cells: values are in Row 2, Columns A–E
        pe = sheet['A2'].value
        pb = sheet['B2'].value
        roe = sheet['C2'].value
        debt_eq = sheet['D2'].value
        mcap = sheet['E2'].value

        return (
            f"📊 {stock_name.upper()} Fundamentals:\n"
            f"P/E Ratio: {pe}\n"
            f"P/B Ratio: {pb}\n"
            f"ROE: {roe}\n"
            f"Debt/Equity: {debt_eq}\n"
            f"Market Cap: {mcap}"
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


