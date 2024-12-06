import pandas as pd
import yfinance as yf 
from yahoofinancials import YahooFinancials

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def stocks(start_date='2014-11-20', end_date='2024-11-20'):
    bio_tickers = ["GSK", "PFE"]
    yahoo_financials = YahooFinancials(bio_tickers)
    data = yahoo_financials.get_historical_price_data(start_date=start_date, 
                                                  end_date=end_date, 
                                                  time_interval='daily')
    df = pd.DataFrame({
        a: {x['formatted_date']: x['adjclose'] for x in data[a]['prices']} for a in bio_tickers})

    df.to_csv("data/{}.csv".format(str(bio_tickers)), index=False)
    return

if __name__ == "__main__":
    stocks()