import pandas as pd

def ccxt_ohlcv_to_dataframe(ohlcv):
    """ Converts cctx ohlcv data from list of lists to dataframe. """
    df = pd.DataFrame(ohlcv)
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['time'] * 1000000, infer_datetime_format=True)
    return df

def klinesFilter(df):
    klines = [
            'Open time',
            'open',
            'high',
            'low',
            'close',
            'Volume',
            'Close time',
            'Quote asset volume',
            'Number of trades',
            'Taker buy base asset volume',
            'Taker buy quote asset volume',
            'ignore'
    ]
    df.columns = klines
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df['Close time'] = pd.to_datetime(df['Close time'], unit='ms')
    df['Open time'] = df['Open time'].apply( lambda x: str(x) )
    df['Close time'] = df['Close time'].apply( lambda x: str(x) )
    df['Close time']  = df['Close time'].apply(lambda x: x[:19])    # 1h,1m timeframe
    # df['close_time']  = df['close_time'].apply(lambda x: x[:10])  # 1d timeframe
    pd.options.display.float_format = '{:.8f}'.format
    df['Open time'] = pd.to_datetime(df['Open time'])
    df['Close time'] = pd.to_datetime(df['Close time'])
    df.set_index(['Open time'], inplace=True)
    df.drop(['ignore'], axis=1, inplace=True)
    return df