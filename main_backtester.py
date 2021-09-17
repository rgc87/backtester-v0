import  pandas      as      pd
from    Backtester  import  Backtester
from    utils       import  klinesFilter
from    strategies  import  BBStrategy
import  re


# IMPORT DATA SOURCES
pathFile                = '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df                      = pd.read_csv(pathFile)
df                      = klinesFilter(df, tf='1h')
df                      = df.iloc[-6000:-1]

start_date              = df.index[0]
end_date                = df.index[-1]
elapsed_time            = start_date-end_date

# Show ROI
first_price             = df.close.iloc[0]
last_price              = df.close.iloc[-1]
bh_roi                  = (( last_price / first_price )-1)*100

pairNamePattern         = re.compile('[A-Z]{6,}')
symbol                  = pairNamePattern.search(pathFile).group()
# *** -------------------------------------------
# INDICATORS SETUP
bb_len                  = 50
n_std                   = 1.8
rsi_len                 = 24
rsi_overbought          = 60
rsi_oversold            = 47

strategy                = BBStrategy(
                                        bb_len,
                                        n_std,
                                        rsi_len,
                                        rsi_overbought,
                                        rsi_oversold
)
strategy.setUp(df)
# *** -------------------------------------------
# BACKTEST PARAMETERS
initial_balance         = 1000
leverage                = 5
trailing_stoploss       = True
entry_amount_percentage = 0.05

showBinnacle            = False
plotOnNewWindow         = True

bullMarket              = False
bearMarket              = True

tpLong                  = lambda n : (n/100)+1
tpShort                 = lambda n : (100-n)/100
slLong                  = lambda n : (100-n)/100
slShort                 = lambda n : (n/100)+1

tp_long                 = tpLong  (8)
tp_short                = tpShort (5)
sl_long                 = slLong  (4)
sl_short                = slShort (3)
# *** ---------------------------------------------------------------
tryback = Backtester(
                    initial_balance,
                    leverage,
                    trailing_stoploss,
                    entry_amount_percentage,
                    showBinnacle,
                    plotOnNewWindow,
                    bullMarket,
                    bearMarket
)
# BACKTEST
tryback.__backtesting__(
                        df,
                        strategy,
                        tp_long,
                        tp_short,
                        sl_long,
                        sl_short,
)
# *** OUTPUT, PRINTS-------------------------------------------------
parameters_genes = {
    'bb_len'                  : f'{int(bb_len)}',
    'n_std'                   : f'{float(n_std):.1f}',
    'rsi_len'                 : f'{int(rsi_len)}',
    'rsi_overbought'          : f'{int(rsi_overbought)}',
    'rsi_oversold'            : f'{int(rsi_oversold)}',
    'tp_long'                 : f'{(tp_long-1)*100:.2f} %',
    'tp_short'                : f'{((tp_short)*100)-100:.2f} %',
    'sl_long'                 : f'{((sl_long)*100)-100:.2f} %',
    'sl_short'                : f'{(sl_short-1)*100:.2f} %'
}
parameters_discretionary = {
    'initial_balance'         : initial_balance,
    'entry_amount_percentage' : entry_amount_percentage,
    'leverage'                : leverage,
    'trailing_stoploss'       : trailing_stoploss,
    'bullMarket'              : bullMarket,
    'bearMarket'              : bearMarket
}
output          =    tryback.return_results(symbol, start_date, end_date)
gross_profit    =    output['balance']
net_profit      =    output['profit_after_fees']
strategy_roi    =    (((net_profit+initial_balance) / initial_balance)-1)*100

print(f'''
Backtest results on:
{pd.DataFrame.from_dict(
                        output, orient='index')}

Genetic parameters:
{pd.DataFrame.from_dict(
                        parameters_genes, orient='index')}

Discretionary parameters:
{pd.DataFrame.from_dict(
                        parameters_discretionary, orient='index')}
Strategy, roi       : %{strategy_roi :.2f}
Buy and Hold, roi   : %{bh_roi:.2f}
Price range         : {first_price} -> {last_price}
''')
