import pandas as pd
from Backtester import Backtester
from utils import klinesFilter
from stratcode import BBStrategy
import re


# IMPORT DATA SOURCES
pathFile = '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df = pd.read_csv(pathFile)
df = klinesFilter(df, tf='1h')
df = df.iloc[30000:-1]

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
bb_len          = 41
n_std           = 2.0
rsi_len         = 30
rsi_overbought  = 72
rsi_oversold    = 46

tp_long     =   (8/100)+1       #1,09 -> +9%
tp_short    =   (100-9)/100     #0,97 -> -3%
sl_long     =   (100-3)/100     #0,99 -> -1%
sl_short    =   (4/100)+1       #1,04 -> +4%

strategy = BBStrategy(
    bb_len,
    n_std,
    rsi_len,
    rsi_overbought,
    rsi_oversold
)
strategy.setUp(df)

# BACKTEST ATRIBUTES
initial_balance     = 1000
leverage            = 10
trailing_stop_loss  = True
entry_amount_p      = 0.05

showBinnacle        = True
plotOnNewWindow     = False

tryback = Backtester(
    initial_balance,
    leverage,
    trailing_stop_loss,
    entry_amount_p,
    showBinnacle,
    plotOnNewWindow
)

# BACKTEST PARAMETERS
tryback.__backtesting__(
    df,
    strategy,
    tp_long,
    tp_short,
    sl_long,
    sl_short,
)
# *** *** *** *** *** *** *** *** *** *** *** *** *** ***
genes = [
    bb_len,
    n_std,
    rsi_len,
    rsi_overbought,
    rsi_oversold,
    tp_long,
    tp_short,
    sl_long,
    sl_short
]
output      = tryback.return_results(symbol, start_date, end_date)
results     = pd.DataFrame.from_dict(output, orient='index')
gross_profit= output['balance']
net_profit  = output['profit_after_fees']
strategy_roi= ( ((net_profit+initial_balance) / initial_balance)-1 ) *100
print(results)
print(genes)
print(f"""
Strategy, roi       : %{strategy_roi :.2f}
Buy and Hold, roi   : %{bh_roi:.2f}
Price range         : {first_price} -> {last_price}""")
