import pandas as pd
import numpy as np


class Backtester():
	def __init__(self, initial_balance, leverage, trailing_stop_loss, entry_amount_p):
		self.initial_balance = initial_balance
		self.balance = initial_balance
		self.amount = 0
		self.leverage = leverage
		self.fee_cost = 0.02 / 100	#Binance

		self.entry_amount_p = entry_amount_p	#Entry amount percentage constant
		self.entry_amount = self.balance * self.entry_amount_p * self.leverage

		self.profit = []
		self.drawdown = []
		self.winned = 0
		self.lossed = 0

		self.num_operations = 0
		self.num_longs = 0
		self.num_shorts = 0

		self.is_long_open = False
		self.is_short_open = False

		self.trailing_stop_loss = trailing_stop_loss
		self.from_opened = 0


	def reset_results(self):
		self.balance = self.initial_balance
		self.amount = 0
		self.profit = []
		self.drawdown = []
		self.winned = 0
		self.lossed = 0
		self.num_operations = 0
		self.num_longs = 0
		self.num_shorts = 0
		self.is_long_open = False
		self.is_short_open = False
		self.from_opened = 0


	def open_position(self, price, side, from_opened = 0):
		self.num_operations += 1
		if side == 'long':
			self.num_longs += 1
			# comment
			if self.is_short_open:
				self.close_position(price)
			if self.is_long_open:
				self.long_open_price = (self.long_open_price + price)/2
				self.amount += self.entry_amount/price
			else:
				self.is_long_open = True
				self.long_open_price = price
				self.amount = self.entry_amount/price
		elif side == 'short':
			self.num_shorts += 1
			# comment
			if self.is_long_open:
				self.close_position(price)
			if self.is_short_open:
				self.short_open_price = (self.short_open_price + price)/2
				self.amount += self.entry_amount/price
			else:
				self.is_short_open = True
				self.short_open_price = price
				self.amount = self.entry_amount/price
		# self.amount = self.entry_amount/price
		if self.trailing_stop_loss:
			self.from_opened = from_opened


	def close_position(self, price):
		self.num_operations += 1
		if self.is_long_open:
			result = self.amount * (price - self.long_open_price)
			self.is_long_open = False
			self.long_open_price = 0
		elif self.is_short_open:
			result = self.amount * (self.short_open_price - price)
			self.is_short_open = False
			self.short_open_price = 0
		self.profit.append(result)
		self.balance += result
		if result > 0:
			self.winned += 1
			self.drawdown.append(0)
		else:
			self.lossed += 1
			self.drawdown.append(result)
		self.take_profit_price = 0
		self.stop_loss_price = 0


	def set_take_profit(self, price, tp_long, tp_short):
		self.tp_long = tp_long
		if self.is_long_open:
			self.take_profit_price = price * tp_long
		elif self.is_short_open:
			self.take_profit_price = price * tp_short


	def set_stop_loss(self, price, sl_long, sl_short):
		if self.is_long_open:
			self.stop_loss_price = price * sl_long
		if self.is_short_open:
			self.stop_loss_price = price * sl_short


	def return_results(self, symbol, start_date, end_date):
		profit = sum(self.profit)
		drawdown = sum(self.drawdown)
		fees = (abs(profit) * self.fee_cost * self.num_operations)
		results = {
			'symbol' : symbol,
			'start_date': start_date,
			'end_date': end_date,
			'balance' : self.balance,
			'profit' :	profit,
			'drawdown': drawdown,
			'profit_after_fees': profit - fees,
			'num_operations' : self.num_operations,
			'num_long' : self.num_longs,
			'num_shorts': self.num_shorts,
			'winned' : self.winned,
			'lossed' : self.lossed
		}
		if self.num_operations > 0 and (self.winned + self.lossed) > 0:
			winrate = self.winned / (self.winned + self.lossed)
			results['winrate'] = winrate
			results['fitness_function'] = \
				(self.num_longs + self.num_shorts) * (profit - abs(drawdown)) \
				* winrate / self.num_operations
		else:
			results['winrate'] = 0
			results['fitness_function'] = 0
		return results


	def __backtesting__(self, df, strategy, tp_long, tp_short, sl_long, sl_short):
		high = df['high']
		close = df['close']
		low = df['low']
		for i in range(len(df)): #probar con itertuples()
			if self.balance > 0:
				if strategy.checkLongSignal(i):
					self.open_position(price = close[i], side = 'long', from_opened = i)
					self.set_take_profit(price = close[i], tp_long=tp_long, tp_short=tp_short)
					self.set_stop_loss(price = close[i], sl_long=sl_long, sl_short=sl_short)
				elif strategy.checkShortSignal(i):
					self.open_position(price = close[i], side = 'short', from_opened = i)
					self.set_take_profit(price = close[i], tp_long=tp_long, tp_short=tp_short)
					self.set_stop_loss(price = close[i], sl_long=sl_long, sl_short=sl_short)
				else:
					if self.trailing_stop_loss  and (self.is_long_open or self.is_short_open):
						new_max = high[self.from_opened:i].max()
						previous_stop_loss = self.stop_loss_price
						self.set_stop_loss(price = new_max, sl_long=sl_long, sl_short=sl_short)
						if previous_stop_loss > self.stop_loss_price:
							self.stop_loss_price = previous_stop_loss
					if self.is_long_open:
						if high[i] >= self.take_profit_price:
							self.close_position(price = self.take_profit_price)
						elif low[i] <= self.stop_loss_price:
							self.close_position(price = self.stop_loss_price)
					elif self.is_short_open:
						if high[i] >= self.stop_loss_price:
							self.close_position(price = self.stop_loss_price)
						elif low[i] <= self.take_profit_price:
							self.close_position(price = self.take_profit_price)
