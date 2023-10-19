

from prettytable import PrettyTable
from datetime import datetime
import requests
import time
import json
import os
import csv

TRADIER_API_ENDPOINT_QUOTES = "https://api.tradier.com/v1/markets/quotes"
TRADIER_API_ENDPOINT_OPTIONS = "https://api.tradier.com/v1/markets/options/chains"
TRADIER_API_KEY="<<YOUR_API_KEY>>"

HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}",
    "Accept": "application/json"
}

def fetch_current_price(ticker):
    response = requests.get(TRADIER_API_ENDPOINT_QUOTES, headers=HEADERS, params={"symbols": ticker})
    data = response.json()
    
    if 'quotes' in data and 'quote' in data['quotes']:
        return data['quotes']['quote']['last']
    else:
        print(f"Unexpected data format for ticker {ticker}: {data}")
        return None
    
def fetch_options_data(ticker):
    # Get today's date in the required format
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Fetch options data for today's date
    params = {
        "symbol": ticker,
        "expiration": today_date,
        "greeks": "true"
    }
    response = requests.get(TRADIER_API_ENDPOINT_OPTIONS, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return data['options']['option']
        except json.JSONDecodeError:
            print(f"Failed to decode JSON for ticker {ticker}. Response: {response.text}")
            return []
    else:
        print(f"Error fetching options data for ticker {ticker}. Status code: {response.status_code}. Response: {response.text}")
        return []



def nearest_strike_options(ticker, price, options_data):
    # Filter options that are within $1 from the current price
    nearest_options = [opt for opt in options_data if abs(opt['strike'] - price) <= 1.0]
    
    return nearest_options


def display_table(price, options):
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console screen

    table = PrettyTable()
    table.field_names = ["Ticker", "Current Price", "Strike", "Type", "Last", "Delta", "Gamma", "Theta", "Vega"]

    for option in options:
        table.add_row([
            "SPY",
            f"${price:.2f}",
            option['strike'],
            option['option_type'],
            option['last'],
            round(option['greeks']['delta'], 4),
            round(option['greeks']['gamma'], 4),
            round(option['greeks']['theta'], 4),
            round(option['greeks']['vega'], 4)
        ])

    print(table)

def write_to_csv(price, options):
    with open('options_data.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        
        for option in options:
            row = [
                "SPY",
                f"{price:.2f}",
                option['strike'],
                option['option_type'],
                option['last'],
                option['greeks']['delta'],
                option['greeks']['gamma'],
                option['greeks']['theta'],
                option['greeks']['vega']
            ]
            writer.writerow(row)

if __name__ == "__main__":
    # Create CSV file with headers if it doesn't exist
    if not os.path.exists('options_data.csv'):
        with open('options_data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Ticker", "Current Price", "Strike", "Type", "Last", "Delta", "Gamma", "Theta", "Vega"])

    while True:
        ticker = "SPY"
        current_price = fetch_current_price(ticker)
        options_data = fetch_options_data(ticker)
        selected_options = nearest_strike_options(ticker, current_price, options_data)
        
        display_table(current_price, selected_options)
        write_to_csv(current_price, selected_options)  # Write the fetched data to CSV
        time.sleep(0.5)
