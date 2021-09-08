import pandas as pd
import numpy as np


class Backtester():
	def __init__(self,
				initial_balance,
				leverage,
				trailing_stop_loss,
				entry_amount_p,
				showBinnacle,
				plotOnNewWindow
	):
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

		self.margin_edge = 100
		self.margin_rate = 1-((self.margin_edge - self.leverage) / self.leverage) / 100


		self.showBinnacle = showBinnacle
		self.plotOnNewWindow = plotOnNewWindow
		self.archive = []
		self.binnacle ={
				'indexID' : int(),
				'orderID'	:	0,
				'timestamp' : str(),
				'operation type' : [],		# long/short
				'operation result' : [], 	# win/loss
				'flag' : [],
				'balance' : [],
				'P_&_L' : [],
				'tp' : [],
				'sl' : [],
				'entry price' : int(),
				'exit price' : [],
				'entry amount' : [], 	# [usd, btc]
				'leverage' : self.leverage, 	# [usd, btc]
				'liquidation price' : 1, 	# [usd, btc]
				'hlc' : []
				# "on market" : bool(),
				,' *** *** end of line *** *** ' : ' *** *** *** *** '
		}

	#  @plotOnNewWindow
			#  def archiveManager(self, binnacle):
			# 		return binnacles


	def saveAndClearBinn(self):
		# Storage dictionary on a list
		self.archive.append( self.binnacle.copy() )
		# Reset values
		self.binnacle['timestamp'] = str()
		self.binnacle['operation type'] = []
		self.binnacle['operation result'] = []
		self.binnacle['flag'] = []
		self.binnacle['balance'] = []
		self.binnacle['P_&_L'] = []
		self.binnacle['tp'] = []
		self.binnacle['sl'] = []
		self.binnacle['entry price'] = int()
		self.binnacle['exit price'] = []
		self.binnacle['entry amount'] = []
		self.binnacle['liquidation price'] = 1
		self.binnacle['hlc'] = []


	def parseArchives(self,archive):
		# recibe la lista y retorna un pandas DF ??
		# df = pd.DataFrame(data='' , columns=' ')
		pass


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
		self.num_operations += 1 #será necesario contar los cierres de esta forma ?
		self.isEntry = True
		self.binnacle['operation type'].append('from open_position( is entry )')
		self.binnacle['orderID'] += 1
		if side == 'long':
			self.num_longs += 1
			self.binnacle['operation type'].append('from open_position( is Long )')
			# comment
			if self.is_short_open:
				self.close_position(price)
				self.binnacle['flag'].append('from open_position( close previous short )')
			if self.is_long_open:
				self.long_open_price = (self.long_open_price + price)/2
				self.amount += self.entry_amount/price
				self.binnacle['flag'].append('from open_position( pyramid )')
			else:
				self.is_long_open = True
				self.long_open_price = price
				self.amount = self.entry_amount/price
				self.binnacle['flag'].append('from open_position( first on chain? )')

		elif side == 'short':
			self.num_shorts += 1
			self.binnacle['operation type'].append('from open_position( is Short )')
			# comment
			if self.is_long_open:
				self.close_position(price)
				self.binnacle['flag'].append('from open_position( close previous long )')
			if self.is_short_open:
				self.short_open_price = (self.short_open_price + price)/2
				self.amount += self.entry_amount/price
				self.binnacle['flag'].append('from open_position( pyramid )')
			else:
				self.is_short_open = True
				self.short_open_price = price
				self.amount = self.entry_amount/price
				self.binnacle['flag'].append('from open_position( first on chain? )')
		# self.amount = self.entry_amount/price

		if self.trailing_stop_loss:
			self.from_opened = from_opened


	def close_position(self, price):
		self.num_operations += 1
		self.isExit = True
		self.binnacle['operation type'].append('from close_position( is exit )')

		if self.is_long_open:
			result = self.amount * (price - self.long_open_price)
			self.binnacle['flag'].append('from close_position( close previous long )')
			self.is_long_open = False
			self.long_open_price = 0

		elif self.is_short_open:
			result = self.amount * (self.short_open_price - price)
			self.binnacle['flag'].append('from close_position( close previous short )')
			self.is_short_open = False
			self.short_open_price = 0

		self.profit.append(result)
		self.balance += result

		if result > 0:
			self.winned += 1
			self.drawdown.append(0)
			self.binnacle['operation result'].append(' *** *** winned *** *** ')
		else:
			self.lossed += 1
			self.drawdown.append(result)
			self.binnacle['operation result'].append(' *** *** lossed *** *** ')

		self.take_profit_price = 0
		self.stop_loss_price = 0



	def set_take_profit(self, price, tp_long, tp_short):
		# self.tp_long = tp_long
		if self.is_long_open:
			self.take_profit_price = price * tp_long
			self.binnacle['tp'].append( f' tp_long {self.take_profit_price}' )
		elif self.is_short_open:
			self.take_profit_price = price * tp_short
			self.binnacle['tp'].append( f' tp_short {self.take_profit_price}' )


	def set_stop_loss(self, price, sl_long, sl_short):
		if self.is_long_open:
			self.stop_loss_price = price * sl_long
			self.binnacle['sl'].append( f' sl_long {self.stop_loss_price}' )
		if self.is_short_open:
			self.stop_loss_price = price * sl_short
			self.binnacle['sl'].append( f' sl_short {self.stop_loss_price}' )

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


	def __backtesting__(self,
						df,
						strategy,
						tp_long,
						tp_short,
						sl_long,
						sl_short):
		high = df['high']
		close = df['close']
		low = df['low']

		for i in range(len(df)): #probar con itertuples()

			if self.balance > 0:
				self.binnacle['balance'].append(self.balance)
				self.binnacle['hlc'].append([high[i], low[i], close[i]])

				if strategy.checkLongSignal(i):
					self.open_position(price = close[i], side = 'long', from_opened = i)

					self.binnacle['entry price'] = close[i] # *** buy long price / enter long price
					self.margin_call = self.margin_rate * self.binnacle['entry price']
					self.binnacle['liquidation price'] = self.margin_call
					self.binnacle['entry amount'].append(self.amount)
					self.binnacle['entry amount'].append(self.amount * close[i])

					self.set_take_profit(price = close[i], tp_long=tp_long, tp_short=tp_short)
					self.set_stop_loss(price = close[i], sl_long=sl_long, sl_short=sl_short)

				elif strategy.checkShortSignal(i):
					self.open_position(price = close[i], side = 'short', from_opened = i)

					self.binnacle['entry price'] = close[i] # *** buy short price / enter short price
					self.margin_call = (self.margin_rate+1) * self.binnacle['entry price']
					self.binnacle['liquidation price'] = self.margin_call
					self.binnacle['entry amount'].append(self.amount)
					self.binnacle['entry amount'].append(self.amount * close[i])

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

			else:
				print('*** *** *** *** *** *** BANKRUPTCY *** *** *** *** *** ***')

			# *** *** BINNACLE REGISTER start	***
			self.binnacle['indexID']= i
			self.binnacle['timestamp'] = df.index[i]
			self.binnacle['balance'].append(self.balance) #balance after operations

			# *** Profit and loss when exit operations
			if len(self.binnacle['balance'])>1:
				if self.binnacle['balance'][0] < self.binnacle['balance'][1]:
					self.binnacle['P_&_L'].append( self.binnacle['balance'][1] - self.binnacle['balance'][0] )
				elif self.binnacle['balance'][0] > self.binnacle['balance'][1]:
					self.binnacle['P_&_L'].append( self.binnacle['balance'][1] - self.binnacle['balance'][0] )
			self.binnacle['balance'].remove( self.binnacle['balance'][0] )

			# *** Show exit price , orderID
			if len(self.binnacle['operation type']) > 0:
				if self.binnacle['operation type'][0] == 'from close_position( is exit )':
					self.binnacle['exit price'].append( close[i] )

			if self.is_long_open:
				if close[i] <= self.binnacle['liquidation price']:
					print('marginCALL',' index: ', i)
			elif self.is_short_open:
				if close[i] >= self.binnacle['liquidation price']:
					print('marginCALL',' index: ', i)

			# *** ***	BINNACLE REGISTER END *** *** *** ***
			self.saveAndClearBinn()
			# *** RESET VALUES ***


		# *** *** *** *** *** SHOW BINNACLE start *** *** *** *** ***
		if self.showBinnacle:
			# print(len(self.archive))
			# print('show Binnacle function')
			for b in self.archive:
				if b['indexID'] > 0: # filtro
					b['orderID'] = str(b['orderID'])+' -(mkt.entry)'
					if len(self.binnacle['operation type']) > 0:
						if b['operation type'][0] != 'from open_position( is entry )':
							b['orderID'] = '_'
					for k,v in b.items():
						print(k,'\t',v)


		# *** agregar columnas al dataframe
		balances = []
		for b in self.archive:
			try:
				balances.append( b['balance'][0] )
				df['c_balances'] = balances
			except:
				IndexError()
				continue
		# *** agregar columnas al dataframe

		# *** *** *** *** *** SHOW BINNACLE end *** *** *** *** ***

		"""la funcion parsea
			resetea
			imprime/no imprime
		"""

		#	***	***	*** PLOT start *** ***	#
		if self.plotOnNewWindow:
			import tkinter
			from matplotlib.backends.backend_tkagg import (
				FigureCanvasTkAgg, NavigationToolbar2Tk)
			# Implement the default Matplotlib key bindings.
			from matplotlib.backend_bases import key_press_handler
			from matplotlib.figure import Figure

			def on_key_press(event):
				print("you pressed {}".format(event.key))
				key_press_handler(event, canvas, toolbar)

			def _quit():
				root.quit()     # stops mainloop
				#root.destroy()  # this is necessary on Windows to prevent
								# Fatal Python Error: PyEval_RestoreThread: NULL tstate

			root = tkinter.Tk()
			root.wm_title("Embedding in Tk")

				# *** *** *** desde aqui va el código *** *** ***

			fig = Figure(figsize=(5, 4), dpi=100)
			fig.add_subplot(111).plot( df['c_balances'] )

				# *** *** *** HASTA quí *** *** ***

			canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
			canvas.draw()
			canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

			toolbar = NavigationToolbar2Tk(canvas, root)
			toolbar.update()
			canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

			canvas.mpl_connect("key_press_event", on_key_press)

			button = tkinter.Button(master=root, text="Quit", command=_quit)
			button.pack(side=tkinter.BOTTOM)

			tkinter.mainloop()
			# If you put root.destroy() here, it will cause an error if the window is
			# closed with the window manager.
			#	***	***	*** PLOT end *** ***	#
