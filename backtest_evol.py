from GenAlgo import Population
from stratcode import BBStrategy
import pandas as pd
from utils import klinesFilter
import re

# IMPORT DATA SOURCES
pathFile = '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df = pd.read_csv(pathFile)
df = klinesFilter(df,tf='1h')
df = df.iloc[30000:]
start_date = df.index[0]
end_date = df.index[-1]
pairNamePattern = re.compile('[A-Z]{6,}')
symbol = pairNamePattern.search(pathFile).group()
timeframe = '1h'

# BACKTEST PARAMETERS
""" tp_long = 1.025
tp_short = 0.975
sl_long = 0.9
sl_short = 1.01 """

P = Population(
	generation_size = 25,
	n_genes = 9,
	gene_ranges = [
		(40, 60),	# bb_len 			(20, 100)
		(15, 25),	# n_std 			(10, 30)
		(14, 40),	# rsi_len         	(5, 50)
		(75, 95),	# rsi_overbought    (60, 95)
		(25, 50),	# rsi_oversold      (20, 50)
		(5,10),		# tp_long         	(2,10)
		(2,6),		# tp_short         	(2,10)
		(1,4),		# sl_long         	(1,6)
		(1,4)		# sl_short         	(1,6)
	],
	n_best = 5,
	mutation_rate = 0.1,

	initial_balance = 1000, # parametric: (1,10) then map(x,y *100 or 1000) ok
	leverage = 5, # parametric: (1,20) ok
	trailing_stop_loss = False, # parametric: (0,1) boolean ok
	entry_amount_p = 0.05 # parametric: (1, 100) then divide /100
	)
"""
Los  siguientes parámetros:
	initial_balance
	leverage
	trailing_stop_loss
	entry_amount_p
podrían ser ingresados al sorteo si es que, se hace por etapas.
Digamos que son parámetros de 2da (experimentales)
"""
population = P.population
number_of_generations = 10

print(f'''GENETIC ALGORITHM TO OPTIMIZE QUANT STRATEGY
BOLLINGER BANDS - RSI
SYMBOL: {symbol} ~ TIMEFRAME: {timeframe}
''')

the_bests = []
for x in range(number_of_generations):
	for individual in population:
		individual.backtester.reset_results()
		genes = individual.genes

		strategy = BBStrategy(
			bb_len			=	genes[0],
			n_std 			=	genes[1]/10,
			rsi_len 		=	genes[2],
			rsi_overbought 	= 	genes[3],
			rsi_oversold 	= 	genes[4]
		)

		strategy.setUp(df)

		individual.backtester.__backtesting__(
			df,
			strategy,
			tp_long			= genes[5]/100, # step -> 1/100 -> 0.001 -> 0.1%
			tp_short		= genes[6]/100,
			sl_long			= genes[7]/100,
			sl_short		= genes[8]/100
		)
	P.crossover()
	P.mutation()
	population = sorted(
		population,
			key = lambda individual: individual.backtester.return_results(
				symbol = symbol,
				start_date = start_date,
				end_date = end_date,
			)\
			['fitness_function'], reverse = True
	)
	best = population[0].backtester.return_results(
		symbol = symbol,
		start_date = start_date,
		end_date = end_date
	)
	best['genes'] = population[0].genes
	worst = population[-1].backtester.return_results(
		symbol = symbol,
		start_date = start_date,
		end_date = end_date
	)
	output_best = pd.DataFrame.from_dict(best, orient='index')
	output_best = output_best.round(decimals=2) #porque no refleja la modificación ??
	output_worst = pd.DataFrame.from_dict(worst, orient='index')

	# *** *** PERSISTENCIA *** ***
	persistOnMongo = False

	print(f''' GENERATION: {x}
	________________________________________
	BEST INDIVIDUAL:
	{output_best}

	bb_len, n_std, rsi_len,
	rsi_overbought, rsi_oversold
	tp_long, tp_short, sl_long, sl_short
	\n
	WORST INDIVIDUAL:
	{output_worst}
	{population[-1].genes}

	''')

	the_bests.append( best )

if persistOnMongo:
	import pymongo
	from pymongo import MongoClient
	from datetime import datetime

	# PERSISTENCIA
	client = MongoClient()
	db = client.backtest
	collection = db.semillitasBest
	# document = best
	documents = the_bests
	# collection.insert_one( document )

	result = collection.insert_many( documents )
	result.inserted_ids

# BEST RESULT FROM EVOLUTION
print(
	'*** *** *** *** *** BETTER RESULT OVERALL *** *** *** *** *** ',
	pd.DataFrame.from_dict(
		max( the_bests, key= lambda x: x['profit_after_fees'] ),
		orient='index'),
	'\n\n\n',
	'*** END ***'
	'\n\n\n',
)
