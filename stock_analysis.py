import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd

class Stock:
    def __init__(self, start_date='2023-10-01', end_date='2024-01-07'):
        self.start, self.end = start_date, end_date
        self.index_constituents = self.get_symbols()
        self.nifty50_prices = self.get_index()
        self.constituent_prices = self.download_historical_prices()

    def get_symbols(self):
        try:
            url = 'https://en.wikipedia.org/wiki/NIFTY_50'
            response = requests.get(url)
        except:
            print("Error: Failed to retrieve the webpage.")

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'wikitable sortable'})
        except:
            print("Error: Failed to retrieve the constituents table.")

        df = pd.read_html(str(table))[0]
        return df[["Company Name", "Symbol"]]
    
    def get_index(self):
        index_data = yf.download('^NSEI', start=self.start, end=self.end)
        return index_data['Close']

    def download_historical_prices(self):
        symbols = list(self.index_constituent["Symbol"])
        
        # Creating an empty DataFrame to store the closing prices
        closing_prices = pd.DataFrame()

        # Fetching the historical data for each symbol
        for symbol in symbols:
            symbol = symbol + '.NS'
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=self.start, end=self.end)
            hist.index = hist.index.strftime('%Y-%m-%d')
            closing_prices[symbol[:-3]] = hist['Close']
        closing_prices.reset_index(inplace=True)
        closing_prices.rename(columns={'index': 'Date'}, inplace=True)
        return closing_prices

    def CurPrice(self, cur_date):
        pass

    def NDayRet(self, n, cur_date):
        pass

    def DailyRet(self, cur_date):
        pass

    def Last30daysPrice(self, cur_date):
        pass