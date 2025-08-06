import threading
import http.server
import socketserver
import os
import openpyxl
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- Fake server to keep Render alive ---
def run_fake_server():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# --- Read from Excel ---
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

# --- Chart generation with RSI ---
INTERVAL_MAP = {
    '1w': ('1wk', '3mo'),
    '1d': ('1d', '1mo'),
    '5m': ('5m', '5d'),
    '1m': ('1m', '1d'),
}

def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi
    return data

def generate_chart(symbol, timeframe):
    if timeframe not in INTERVAL_MAP:
        return None, "❌ Invalid timeframe. Use 1w, 1d, 5m, or 1m."

    interval, period = INTERVAL_MAP[timeframe]
    data = yf.download(symbol, interval=interval, period=period)
    if data.empty:
        return None, "❌ No data found for this symbol."

    data = compute_rsi(data)
    rsi_data = data['RSI']
    apds = [mpf.make_addplot(rsi_data, panel=1, color='purple', ylabel='RSI')]

    file_name = f"{symbol}_{timeframe}_chart.png"
    mpf.plot(data, type='candle', style='yahoo', volume=True,
             addplot=apds, panel_ratios=(3,1),
             title=f'{symbol.upper()} - {timeframe} Chart with RSI',
             savefig=file_name)
    return file_name, None

# --- Bot message handler ---
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    print(f"Received message: {text}")

    if "fundamental" in text:
        stock = text.split()[0]
        message = get_fundamentals(stock)
        await update.message.reply_text(message)

    elif text.startswith("chart"):
        try:
            parts = text.split()
            symbol = parts[1].upper()
            timeframe = parts[2]
            await update.message.reply_text(f"📊 Generating {symbol} chart [{timeframe}]...")
            chart_file, error = generate_chart(symbol, timeframe)
            if error:
                await update.message.reply_text(error)
            else:
                await update.message.reply_photo(photo=open(chart_file, 'rb'))
                os.remove(chart_file)  # Clean up
        except Exception as e:
            await update.message.reply_text("❌ Error. Use: chart SYMBOL TIMEFRAME (e.g., chart AAPL 1d)")
    else:
        await update.message.reply_text("❓ Use:\n1. TCS fundamental\n2. chart TCS 1d")

# --- Start Bot ---
BOT_TOKEN = os.environ.get("7633874537:AAGSETQ5HWaYI8arJ64Xu0qOSlPOsLzRYHc")  # Set BOT_TOKEN in Render
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
print("🤖 Bot is running... Press Ctrl+C to stop.")
app.run_polling()
