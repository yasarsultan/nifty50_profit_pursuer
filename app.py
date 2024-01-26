import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO
import matplotlib.pyplot as plt
import streamlit as st

class Stock:
    def __init__(self, symbol, start_date='2023-10-01', end_date='2024-01-08'):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.stock_data = self.get_data()
        self.price_data = self.stock_data['Close']

    def get_data(self):
        try:
            data = yf.download(self.symbol, self.start_date, self.end_date)
        except:
            st.write(f"No data found for {self.symbol} between {self.start_date} and {self.end_date}")
            return None
        # data.index = data.index.strftime('%Y-%m-%d')
        data['Daily Return'] = ((data['Close'] - data['Open']) / data['Open']) * 100

        data['1Day Return'] = data['Close'].pct_change().fillna(0)

        prev_days_value = 0
        values_column = []
        for index, row in data.iterrows():
            temp = data['1Day Return'].loc[index] + prev_days_value
            prev_days_value += data['1Day Return'].loc[index]
            values_column.append(temp)
        data['Compound Return'] = values_column
        return data[['Open', 'Close', 'Daily Return', '1Day Return', 'Compound Return']]
        
    def CurPrice(self, cur_date):
        if cur_date in self.price_data.index:
            price = self.price_data.loc[cur_date]
        else:
            price = 0
            st.write(f"This date {cur_date} not present in our data.")
        return price
    
    def NDayRet(self, n, cur_date):
        # Counting only market days
        if cur_date in self.price_data.index:
            cur_row = self.price_data.index.get_loc(cur_date)
            if cur_row >= n:
                price_today = self.price_data.iloc[cur_row]
                price_n_days_ago = self.price_data.iloc[cur_row - n]
                n_day_return = ((price_today - price_n_days_ago) / price_n_days_ago) * 100
                return n_day_return
            else:
                st.write(f"Reduce the value of n from {n}, or change start date to that date to your cur_date{cur_date}.")
        else:
            st.write(f"Either market was closed on {cur_date}, or the given date is not present in our record.")

    def DailyRet(self, cur_date):
        if cur_date in self.stock_data.index:
            open = self.stock_data.loc[cur_date, 'Open']
            close = self.stock_data.loc[cur_date, 'Close']
            returns = ((close - open)/open) * 100
            return returns
        else:
            st.write(f"Either market was closed on {cur_date}, or the given date is not present in our record.")

    def Last30daysPrice(self, cur_date):
        if cur_date in self.price_data.index:
            cur_row = self.price_data.index.get_loc(cur_date)
            if cur_row >= 30:
                price_30_days_ago = self.price_data.iloc[cur_row - 30]
                return price_30_days_ago
        else:
            st.write(f"Either market was closed on {cur_date}, or the given date is not present in our record.")


def get_benchmark(start_date, end_date):
    nifty50 = Stock('^NSEI', start_date, end_date)
    return nifty50

def get_constituents(start_date, end_date):
    try:
        url = 'https://en.wikipedia.org/wiki/NIFTY_50'
        response = requests.get(url)
    except:
        st.write("Error: Failed to retrieve the webpage.")

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable sortable'})
    except:
        st.write("Error: Failed to retrieve the constituents table.")

    df = pd.read_html(StringIO(str(table)))[0]
    df = df[["Company Name", "Symbol"]]

    constituents_data = {}
    for index, row in df.iterrows():
        constituents_data[row['Company Name']] = Stock(str(row['Symbol']+'.NS'), start_date, end_date)

    return constituents_data

def get_active_strategy(constituents_data, cur_date):
    active_stocks = []
    active_stocks_returns = pd.DataFrame()

    prev_month = pd.Timestamp(cur_date).month - 1
    
    for company, stock in constituents_data.items():
        prev_month_rows = stock.stock_data[stock.stock_data.index.month == prev_month]
        if stock.stock_data.loc[prev_month_rows.index.max(), 'Close'] > stock.stock_data.loc[prev_month_rows.index.min(), 'Close']:
            active_stocks.append(company)
            active_stocks_returns[company] = stock.stock_data['Compound Return']

    if len(active_stocks) == 0:
        return ['No positve stock'], None
    else:
        num_columns = len(active_stocks_returns.columns)
        active_stocks_returns['Average'] = active_stocks_returns.sum(axis=1) / num_columns

    return active_stocks, active_stocks_returns['Average']

def plot_ichart(returns1, returns2):
    # Choosing common dates only
    common_dates = returns1.index.intersection(returns2.index)
    benchmark_filtered, stocks_filtered = returns1.loc[common_dates], returns2.loc[common_dates]

    plt.figure(figsize=(10,6))
    plt.plot(benchmark_filtered.index, benchmark_filtered.values, label='Benchmark')
    plt.plot(stocks_filtered.index, stocks_filtered.values, label='Stock selection strategy')
    plt.legend()
    plt.xlabel('Date')
    plt.xticks(rotation = 90)
    plt.ylabel('Returns')
    # plt.show()
    st.pyplot(plt)

def plot_chart(returns1, returns2):
   # Choosing common dates only
   common_dates = returns1.index.intersection(returns2.index)
   benchmark_filtered, stocks_filtered = returns1.loc[common_dates], returns2.loc[common_dates]

   st.line_chart(pd.concat([benchmark_filtered, stocks_filtered], axis=1, keys=['Benchmark', 'Selected stocks']))



def main():
    st.title('Stock Performance Analysis')
    start_date = str(st.date_input("Enter start date in format YYYY-MM-DD: ")).split()[0]
    end_date = str(st.date_input("Enter end date in format YYYY-MM-DD: ")).split()[0]

    if start_date == end_date:
        st.write(f'Please change {start_date} that is start date to get more insights.')
        return
    elif start_date > end_date:
        st.write(f"Please change the start date. It should come before end date.")
        return

    amount = int(st.number_input("Enter the amount: "))
    if amount <= 0:
        st.write("Enter valid amount.")
        return

    cur_date = str(st.date_input("Enter any date to select that month's strategy: ")).split()[0]
    if cur_date <= start_date or cur_date >= end_date:
        st.write("Select different month.")
        return
    
    benchmark = get_benchmark(start_date, end_date)
    index_constituents = get_constituents(start_date, end_date)

    benchmark_returns = benchmark.stock_data['Compound Return']
    selected_stocks, selected_stocks_returns = get_active_strategy(index_constituents, cur_date)
    if selected_stocks[0] != 'No positve stock':
        strategic_returns = selected_stocks_returns
    else:
        selected_stocks_returns = pd.Series(0, index = benchmark_returns.index)

    st.subheader('Comparing Returns: ')
    plot_chart(benchmark_returns, strategic_returns)

    st.subheader("Stocks that are selected for the given month's strategy: ")
    st.write(selected_stocks)

    strategic_returns = selected_stocks_returns * amount + amount
    benchmark_returns = benchmark.stock_data['Compound Return'] * amount + amount
    st.subheader('Invested amount: ')
    plot_ichart(benchmark_returns, strategic_returns)
        
        
if __name__ == '__main__':
    main()