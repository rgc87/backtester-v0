import pandas as pd
import numpy as np


class Backtester():
	def __init__(self,
				initial_balance,
				leverage,
				trailing_stop_loss,
				entry_amount_p,
				showBinnacle,
				plotOnNewWindow,
				bullMarket,
				bearMarket
	):
		self.INITIAL_BALANCE 	= initial_balance
		self.balance 			= initial_balance		#Track closed operations only!
		self.wallet				= initial_balance		#Track operations on Open

		#Base asset, entry amount
		self.amount 			= 0
		self.LEVERAGE 			= leverage
		self.FEE_COST 			= 0.02 / 100			#Binance
		self.ENTRY_AMOUNT_P 	= entry_amount_p		#Entry amount, percentage constant

		#Quoted asset, entry amount
		self.entry_amount 		= lambda : self.wallet * self.ENTRY_AMOUNT_P * self.LEVERAGE

		self.profit 			= []
		self.drawdown 			= []
		self.winned 			= 0
		self.lossed 			= 0

		self.bullMarket 		= bullMarket 			#Booleans
		self.bearMarket 		= bearMarket 			#Booleans

		self.num_operations 	= 0
		self.num_longs 			= 0
		self.num_shorts 		= 0
		self.is_long_open 		= False
		self.is_short_open 		= False

		self.trailing_stop_loss = trailing_stop_loss 	#Boolean
		self.from_opened 		= 0

		self.margin_edge 		= 100
		self.margin_rate 		= 1-((self.margin_edge - self.LEVERAGE) / self.LEVERAGE)/100

		self.showBinnacle 		= showBinnacle 			#Boolean
		self.plotOnNewWindow 	= plotOnNewWindow 		#Boolean
		self.archive 			= [] 					#Store dict(binnacles)

		self.order_id			= 0
		self.take_profit_price 	= float()
		self.stop_loss_price 	= float()
		self.margin_call		= float() #lambda : self.entry_price * self.margin_rate
		self.market_side 		= 'Out of market' 		#Bear, Bull
		self.entry_price		= float()
		self.pyramid_counter	= 0


	def binnacle(self):
		if len(self.operation_type) >0:
			if 'Entry Long' in self.operation_type[0]:
				self.market_side = 'Bull'
			elif 'Entry Short' in self.operation_type[0]:
				self.market_side = 'Bear'

		elif len(self.operation_type)==0 and\
			(self.take_profit_price == 0 and self.stop_loss_price == 0):
				self.market_side = 'Out of market'

		# *** Storage on dictionary
		# binnacle ={
		# 	'timestamp'			: self.timestamp,
		# 	'index_id'			: self.index_id,
		# 	'order_id'			: self.order_id,
		# 	'operation_type'	: (self.operation_type),
		# 	'pyramid_count'		: self.pyramid_counter,
		# 	'entry_price'		: f'{self.entry_price:.2f}',
		# 	'entry_am_base'		: f'{self.entry_amount_base:.8f}',
		# 	'entry_am_quoted'	: f'{self.entry_amount_quoted:.2f}',
		# 	'takeprofit'		: f'{self.take_profit_price:.2f}',
		# 	'stoploss'			: f'{self.stop_loss_price:.2f}',
		# 	'margin_call'		: f'{self.margin_call:.2f}',
		# 	'leverage'			: self.LEVERAGE,
		# 	'sub_operation'		: self.sub_operation,
		# 	'operation_result'	: self.operation_result,
		# 	'profit_loss'		: f'{self.pL:.2f}',
		# 	'wallet'			: f'{self.wallet:.2f}',
		# 	'balance'			: f'{self.balance:.2f}',
		# 	'candles_hlc'		: self.candles,
		# 	'market_side'		: self.market_side
		# }
		# self.archive.append(binnacle)
		print(f'''
		timestamp		: {self.timestamp}
		index_id		: {self.index_id}
		order_id		: {self.order_id}
		operation_type	: {self.operation_type}
		pyramid_count	: {self.pyramid_counter}
		entry_price		: {f'{self.entry_price:.2f}'}
		entry_am_base	: {f'{self.entry_amount_base:.8f}'}
		entry_am_quoted : {f'{self.entry_amount_quoted:.2f}'}
		takeprofit		: {f'{self.take_profit_price:.2f}'}
		stoploss		: {f'{self.stop_loss_price:.2f}'}
		margin_call		: {f'{self.margin_call:.2f}'}
		leverage		: {self.LEVERAGE}
		sub_operation	: {self.sub_operation}
		operation_result: {self.operation_result}
		profit_loss		: {f'{self.pL:.2f}'}
		wallet			: {f'{self.wallet:.2f}'}
		balance			: {f'{self.balance:.2f}'}
		candles_hlc		: {self.candles}
		market_side		: {self.market_side}''')

		# *** Reset values
		self.operation_type.clear()
		self.flags.clear()


	def binnaclePrint(self):
		for b in self.archive[100:-1]:
			print(f'''
			timestamp		:{b['timestamp']}
			index_id		:{b['index_id']}
			order_id		:{b['order_id']}
			operation_type	:{b['operation_type']}
			pyramid_count	:{b['pyramid_count']}
			entry_price		:{b['entry_price']}
			entry_am_base	:{b['entry_am_base']}
			entry_am_quoted	:{b['entry_am_quoted']}
			takeprofit		:{b['takeprofit']}
			stoploss		:{b['stoploss']}
			margin_call		:{b['margin_call']}
			leverage		:{b['leverage']}
			sub_operation	:{b['sub_operation']}
			operation_result:{b['operation_result']}
			profit_loss		:{b['profit_loss']}
			wallet			:{b['wallet']}
			balance			:{b['balance']}
			candles_hlc		:{b['candles_hlc']}
			market_side		:{b['market_side']}''')


	def reset_results(self):
		self.balance 		= self.INITIAL_BALANCE
		self.amount 		= 0
		self.profit 		= []
		self.drawdown 		= []
		self.winned 		= 0
		self.lossed 		= 0
		self.num_operations = 0
		self.num_longs 		= 0
		self.num_shorts 	= 0
		self.is_long_open 	= False
		self.is_short_open 	= False
		self.from_opened 	= 0


	def open_position(self, price, side, from_opened = 0):
		self.num_operations += 1
		self.order_id 		+= 1

		if self.bullMarket:
			if side == 'long':
				self.num_longs 	+= 1

				if self.bearMarket:																	#Close previous
					if self.is_short_open:
						self.sub_operation.append('Close previous, short')
						self.close_position(price)

				if self.bullMarket:
					if self.is_long_open:															#Then make a pyramid
						self.operation_type.append('Entry Long, pyramid**')
						self.pyramid_counter 				   += 1
						self.long_open_price				    = (self.long_open_price + price)/2 	# Recalculo
						self.entry_price						= self.long_open_price
						self.amount 						   += self.entry_amount()/price 		# Recalculo

						self.entry_amount_quoted 				= self.entry_amount()
						self.entry_amount_base 					= self.amount
						self.wallet					 		   -= self.entry_amount()/self.LEVERAGE
					else:
						self.operation_type.append('Entry Long, first*')							# First on chain
						self.is_long_open 					 	= True
						self.long_open_price 				 	= price
						self.entry_price						= self.long_open_price
						self.amount 						 	= self.entry_amount()/price

						self.entry_amount_quoted 				= self.entry_amount()
						self.entry_amount_base 					= self.amount
						self.wallet					 		   -= self.entry_amount()/self.LEVERAGE
				self.margin_call = self.entry_price*self.margin_rate

		if self.bearMarket:
			if side == 'short':
				self.num_shorts += 1

				if self.bullMarket:																	#Close previous
					if self.is_long_open:
						self.sub_operation.append('Close previous, long')
						self.close_position(price)

				if self.bearMarket:
					if self.is_short_open:															#Then make a pyramid
						self.operation_type.append('Entry Short, pyramid**')
						self.pyramid_counter 				   += 1
						self.short_open_price	 				= (self.short_open_price + price)/2 #Recálculo
						self.entry_price						= self.short_open_price
						self.amount 			 			   += self.entry_amount()/price			#Recálculo

						self.entry_amount_quoted 				= self.entry_amount()
						self.entry_amount_base 					= self.amount
						self.wallet					 		   -= self.entry_amount()/self.LEVERAGE
					else:																			# First on chain
						self.operation_type.append('Entry Short, first*')

						self.is_short_open 					    = True
						self.short_open_price 				    = price
						self.entry_price						= self.short_open_price
						self.amount 						    = self.entry_amount()/price

						self.entry_amount_quoted 				= self.entry_amount()
						self.entry_amount_base 					= self.amount
						self.wallet					 		   -= self.entry_amount()/self.LEVERAGE
				self.margin_call = self.entry_price*(self.margin_rate+1)

		if self.trailing_stop_loss:
			self.from_opened = from_opened


	def close_position(self, price):
		self.num_operations += 1

		if self.bullMarket:
			if self.is_long_open:
				result					= self.amount*(price - self.long_open_price)
				self.is_long_open 		= False
				self.long_open_price 	= 0

		if self.bearMarket:
			if self.is_short_open:
				result 					= self.amount*(self.short_open_price - price)
				self.is_short_open 		= False
				self.short_open_price 	= 0

		self.profit.append(result)
		self.balance 					+= result
		self.wallet				 		= self.balance

		if result > 0:
			self.winned 				+= 1
			self.drawdown.append(0)
			self.operation_result		= '*** *** WINNED *** ***'
		else:
			self.lossed 				+= 1
			self.drawdown.append(result)
			self.operation_result		= '*** *** LOSSED *** ***'

		self.pL							= result
		self.take_profit_price 			= 0
		self.stop_loss_price 			= 0
		self.margin_call				= float()
		self.pyramid_counter			= 0

	def set_take_profit(self, price, tp_long, tp_short):
		# self.tp_long = tp_long
		if self.bullMarket:
			if self.is_long_open:
				self.take_profit_price 	= price * tp_long
		if self.bearMarket:
			if self.is_short_open:
				self.take_profit_price 	= price * tp_short


	def set_stop_loss(self, price, sl_long, sl_short):
		if self.bullMarket:
			if self.is_long_open:
				self.stop_loss_price 	= price * sl_long
		if self.bearMarket:
			if self.is_short_open:
				self.stop_loss_price	= price * sl_short


	def return_results(self, symbol, start_date, end_date):
		profit 		= sum(self.profit)
		drawdown 	= sum(self.drawdown)
		fees 		= (abs(profit) * self.FEE_COST * self.num_operations)
		results 	= {
			'symbol'			: symbol,
			'start_date'		: start_date,
			'end_date'			: end_date,
			'balance'			: self.balance,
			'profit'			: profit,
			'drawdown'			: drawdown,
			'profit_after_fees'	: profit - fees,
			'num_operations'	: self.num_operations,
			'num_long'			: self.num_longs,
			'num_shorts'		: self.num_shorts,
			'winned'			: self.winned,
			'lossed'			: self.lossed
		}
		# Calculate winrate%
		if self.num_operations > 0 and (self.winned + self.lossed) > 0:
			winrate = self.winned / (self.winned + self.lossed)
			results['winrate'] 			= winrate
			results['fitness_function'] = \
				(self.num_longs + self.num_shorts) * (profit - abs(drawdown)) \
				* winrate / self.num_operations
		else:
			results['winrate'] 			= 0
			results['fitness_function'] = 0
		return results


	def __backtesting__(self,
						df,
						strategy,
						tp_long,
						tp_short,
						sl_long,
						sl_short):
		high 	= df['high']
		close	= df['close']
		low 	= df['low']

		for i in range(len(df)): #probar con itertuples()
			if self.balance > 0:
				self.index_id				= i
				self.timestamp 				= df.index[i]
				self.candles 				= [high[i],low[i],close[i]]
				# self.market_side 			= 'out of market'
				self.operation_type			= []
				self.sub_operation			= []
				self.flags					= []
				self.operation_result		= str()
				self.entry_amount_base 		= float()
				self.entry_amount_quoted 	= float()
				self.pL						= float()
				# self.entry_price			= float()


				if self.bullMarket:
					if strategy.checkLongSignal(i):
						# if wallet >= entry_amount_p*self.balance:
						self.open_position(
							price 		= close[i],
							side 		= 'long',
							from_opened = i
						)
						# else: continue

						self.set_take_profit(
							price 		=	close[i],
							tp_long		=	tp_long,
							tp_short	=	tp_short
						)
						self.set_stop_loss(
							price 		=	close[i],
							sl_long		=	sl_long,
							sl_short	=	sl_short
						)
				if self.bearMarket:
					if strategy.checkShortSignal(i):
						# if wallet >= entry_amount_p*self.balance:
						self.open_position(
							price 		= close[i],
							side 		= 'short',
							from_opened = i
						)
						# else: continue

						self.set_take_profit(
							price 		=	close[i],
							tp_long		=	tp_long,
							tp_short	=	tp_short
						)
						self.set_stop_loss(
							price 		=	close[i],
							sl_long		=	sl_long,
							sl_short	=	sl_short
						)

				if self.trailing_stop_loss  and (self.is_long_open or self.is_short_open):
					new_max 			= high[self.from_opened:i].max()
					previous_stop_loss 	= self.stop_loss_price
					self.set_stop_loss(
						price 	= new_max,
						sl_long	=sl_long,
						sl_short=sl_short
					)
					if previous_stop_loss > self.stop_loss_price:
						self.stop_loss_price = previous_stop_loss

				if self.bullMarket:
					if self.is_long_open:
						if high[i] >= self.take_profit_price:
							self.close_position(price = self.take_profit_price)
							self.operation_type.append('Exit Long by takeprofit')
						elif low[i] <= self.stop_loss_price:
							self.close_position(price = self.stop_loss_price)
							self.operation_type.append('Exit Long by stoploss')
				if self.bearMarket:
					if self.is_short_open:
						if high[i] >= self.stop_loss_price:
							self.close_position(price = self.stop_loss_price)
							self.operation_type.append('Exit Short by stoploss')
						elif low[i] <= self.take_profit_price:
							self.close_position(price = self.take_profit_price)
							self.operation_type.append('Exit Short by takeprofit')

				# if self.index_id>56 and self.index_id<400:
					self.binnacle()

			else:
				print('\n*** *** *** *** *** *** BANKRUPTCY *** *** *** *** *** ***\n')
				import sys
				sys.exit()
		# *** *** *** *** *** OUT OF FOR CICLE, in range(df) *** *** *** *** ***

		""" if self.showBinnacle:
			self.binnaclePrint() """

		if self.plotOnNewWindow:
			self.__plot__(df)

		# *** *** *** *** *** 								 *** *** *** *** ***

	def __plot__(self,df):
		dframe = df
		# *** Esto hay que hacerlo bien hecho ***
		balances = []
		for b in self.archive:
			try:
				balances.append( b['balance'][0] )
				df['c_balances'] = balances
			except:
				IndexError()
				continue
		#----------------------------------------
		import tkinter
		from matplotlib.backends.backend_tkagg import (
			FigureCanvasTkAgg, NavigationToolbar2Tk)
		# Implement the default Matplotlib key bindings.
		from matplotlib.backend_bases import key_press_handler
		from matplotlib.figure import Figure

		# esto puede ser una lambda
		def on_key_press(event):
			print("you pressed {}".format(event.key))
			key_press_handler(event, canvas, toolbar)

		# esto puede ser una lambda
		def _quit():
			root.quit()     # stops mainloop
			#root.destroy()  # this is necessary on Windows to prevent
							# Fatal Python Error: PyEval_RestoreThread: NULL tstate
		root = tkinter.Tk()
		root.wm_title("Embedding in Tk")
			# *** *** *** desde aqui va el código *** *** ***

		fig = Figure(figsize=(5, 4), dpi=100)
		fig.add_subplot(111).plot( dframe['c_balances'] )

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
