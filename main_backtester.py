import pandas as pd
from Backtester import Backtester
from utils import klinesFilter
from stratcode import BBStrategy
import re


# IMPORT DATA SOURCES
pathFile = '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df = pd.read_csv(pathFile)
df = klinesFilter(df, tf='1h')
df = df.iloc[20000:-1]

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
bb_len = 58
n_std = 2.0
rsi_len = 34
rsi_overbought = 75
rsi_oversold = 40

tp_long =   9/100   #1.05
tp_short =   4/100   #0.096
sl_long =   3/100   #0.098
sl_short =  1/100

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
leverage = 1
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
