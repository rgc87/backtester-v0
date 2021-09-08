import pandas as pd

def ccxt_ohlcv_to_dataframe(ohlcv):
    """ Converts cctx ohlcv data from list of lists to dataframe. """
    df = pd.DataFrame(ohlcv)
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['time'] * 1000000, infer_datetime_format=True)
    return df

def klinesFilter(df, tf):
    klines = [
            'open time',
            'open',
            'high',
            'low',
            'close',
            'volume',
            'close time',
            'quote asset volume',
            'number of trades',
            'taker buy base asset volume',
            'taker buy quote asset volume',
            'ignore'
    ]
    df.columns = klines
    df['open time'] = pd.to_datetime(df['open time'], unit='ms')
    df['close time'] = pd.to_datetime(df['close time'], unit='ms')
    df['open time'] = df['open time'].apply( lambda x: str(x) )
    df['close time'] = df['close time'].apply( lambda x: str(x) )

    if tf == '1d':
        df['close_time']  = df['close_time'].apply(lambda x: x[:10])  # 1d timeframe
    elif tf == '1h' or '1m':
        df['close time']  = df['close time'].apply(lambda x: x[:19])    # 1h,1m timeframe

    pd.options.display.float_format = '{:.8f}'.format
    df['open time'] = pd.to_datetime(df['open time'])
    df['close time'] = pd.to_datetime(df['close time'])
    df.set_index(['open time'], inplace=True)
    df.drop(['ignore'], axis=1, inplace=True)
    return df


# Esto será un decorador
def plotOnNewWindow(archive):
    """
    "Archive" será la lista de diccionarios,
    pasada como argumento dentro del método __backtesting__,
    que es el retorno de la funcion(archive) !!
    """
    def openTkinter(binnacles):
        """El argumento "df" es pasado
        dentro del método __backtesting__

        """
        #ploteo
        pass
    return openTkinter()