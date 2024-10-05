import yfinance as yf
import json

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
      "avgPrice": 134.94,
      "amount": 20.1471,
      "currentPrice": priceVFV
    },
    "VEQT": {
      "avgPrice": 42.71,
      "amount": 38.2796,
      "currentPrice": priceVEQT
    }
  }

  # Calculate total deposit and current value
  totalDeposit = (stocks["VEQT"]["avgPrice"] * stocks["VEQT"]["amount"]) + (stocks["VFV"]["avgPrice"] * stocks["VFV"]["amount"])
  currentValue = (stocks["VEQT"]["currentPrice"] * stocks["VEQT"]["amount"]) + (stocks["VFV"]["currentPrice"] * stocks["VFV"]["amount"])

  totalGain = round((((currentValue - totalDeposit) / totalDeposit) * 100), 2)
  return totalGain

stockUp()
