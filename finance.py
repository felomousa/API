import yfinance as yf
import json
import os
from dotenv import load_dotenv

load_dotenv()

def stockUp():
  tickers = yf.Tickers('VFV.TO VEQT.TO')

  # Fetch ticker info
  infoVFV = tickers.tickers['VFV.TO'].info
  infoVEQT = tickers.tickers['VEQT.TO'].info

  # Use regularMarketPrice instead of bid price
  priceVFV = infoVFV['bid']
  priceVEQT = infoVEQT['bid']

  stocks = {
    "VFV": {
      "avgPrice": float(os.getenv('VFV_AVG_PRICE')),
      "amount": float(os.getenv('VFV_AMOUNT')),
      "currentPrice": priceVFV
    },
    "VEQT": {
      "avgPrice": float(os.getenv('VEQT_AVG_PRICE')),
      "amount": float(os.getenv('VEQT_AMOUNT')),
      "currentPrice": priceVEQT
    }
  }

  # Calculate total deposit and current value
  totalDeposit = (stocks["VEQT"]["avgPrice"] * stocks["VEQT"]["amount"]) + (stocks["VFV"]["avgPrice"] * stocks["VFV"]["amount"])
  currentValue = (stocks["VEQT"]["currentPrice"] * stocks["VEQT"]["amount"]) + (stocks["VFV"]["currentPrice"] * stocks["VFV"]["amount"])

  totalGain = round((((currentValue - totalDeposit) / totalDeposit) * 100), 2)
  return totalGain

stockUp()