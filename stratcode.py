import pandas_ta as ta

class BBStrategy:
	def __init__(self, bb_len, n_std, rsi_len, rsi_overbought, rsi_oversold):
		self.bb_len = bb_len
		self.n_std = n_std
		self.rsi_len = rsi_len
		self.rsi_overbought = rsi_overbought
		self.rsi_oversold = rsi_oversold

	def setUp(self, df):
		bb = ta.bbands(
			close = df['close'],
			length = self.bb_len,
			std = self.n_std
		)
		df['lbb'] = bb.iloc[:,0]
		df['mbb'] = bb.iloc[:,1]
		df['ubb'] = bb.iloc[:,2]
		df['rsi'] = ta.rsi(close = df['close'], length = self.rsi_len)
		self.dataframe = df

	def checkLongSignal(self, i = None):
		df = self.dataframe
		if i == None:
			i = len(df)
		if (df['rsi'].iloc[i] < self.rsi_overbought) and \
			(df['rsi'].iloc[i] > self.rsi_oversold) and \
			(df['low'].iloc[i-1] < df['lbb'].iloc[i-1]) and \
			(df['low'].iloc[i] > df['lbb'].iloc[i]) :
			return True
		return False

	def checkShortSignal(self, i = None):
		df = self.dataframe
		if i == None:
			i = len(df)
		if (df['rsi'].iloc[i] < self.rsi_overbought) and \
			(df['rsi'].iloc[i] > self.rsi_oversold) and \
			(df['high'].iloc[i-1] > df['ubb'].iloc[i-1]) and \
			(df['high'].iloc[i] < df['ubb'].iloc[i]):
			return True
		return False


""" class otra:
	def __init__(self):
		pass """