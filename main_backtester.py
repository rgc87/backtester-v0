import pandas as pd
from Backtester import Backtester
from utils import klinesFilter
from stratcode import BBStrategy
import re


# IMPORT DATA SOURCES
pathFile = '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df = pd.read_csv(pathFile)
df = klinesFilter(df, tf='1h')
df = df.iloc[33000:]

start_date = df.index[0]
end_date = df.index[-1]
elapsed_time = start_date-end_date

# Show ROI
first_price = df.close.iloc[0]
bh_roi = (( df.close.iloc[-1] / df.close.iloc[0] )-1)*100
last_price = df.close.iloc[-1]

pairNamePattern = re.compile('[A-Z]{6,}')
symbol = pairNamePattern.search(pathFile).group()

# STRATEGY SETUP
bb_len = 88
n_std = 2.8
rsi_len = 9
rsi_overbought = 88
rsi_oversold = 22

tp_long = 1.025
tp_short = 0.975
sl_long = 0.9
sl_short = 1.01

strategy = BBStrategy(
    bb_len,
    n_std,
    rsi_len,
    rsi_overbought,
    rsi_oversold
)
strategy.setUp(df)

# BACKTEST ATRIBUTES
initial_balance = 1000
leverage = 10
trailing_stop_loss = False
entry_amount_p = 0.05
tryback = Backtester(
    initial_balance,
    leverage,
    trailing_stop_loss,
    entry_amount_p
)

# BACKTEST PARAMETERS
tryback.__backtesting__(
    df,
    strategy,
    tp_long,
    tp_short,
    sl_long,
    sl_short
)

output = tryback.return_results(symbol, start_date, end_date)
results = pd.DataFrame.from_dict(output, orient='index')
print(results)

print(f'''
    Strategy, roi: \t %{(((output['balance']) / (initial_balance))-1)*100:.2f}
    Buy and Hold, roi: \t %{bh_roi:.2f}
    For: {first_price} -> {last_price}
    ''')
