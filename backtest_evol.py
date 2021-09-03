from GA import Population
from stratcode import BBStrategy
import pandas as pd
from utils import klinesFilter
import re


# IMPORT DATA SOURCES
pathFile = '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df = pd.read_csv(pathFile)
df = klinesFilter(df,tf='1h')
df = df.iloc[33000:]
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
		(20, 100),	# bb_len
		(10, 30),	# n_std
		(5, 50),	# rsi_len
		(60, 95),	# rsi_overbought
		(20, 50),	# rsi_oversold
		(2,10),		# tp_long
		(2,10),		# tp_short
		(1,6),		# sl_long
		(1,6)		# sl_short
	],
	n_best = 5,
	mutation_rate = 0.1
	)
population = P.population
number_of_generations = 5

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
	worst = population[-1].backtester.return_results(
		symbol = symbol,
		start_date = start_date,
		end_date = end_date
	)
	output_best = pd.DataFrame.from_dict(best, orient='index')
	output_worst = pd.DataFrame.from_dict(worst, orient='index')

	print(f''' GENERATION: {x}
	________________________________________
	BEST INDIVIDUAL:
	{output_best}

	{(population[0].genes)[0:5]}
	{list( map( lambda x: x/100 , (population[0].genes)[5:9] ) )}

	bb_len, n_std, rsi_len,
	rsi_overbought, rsi_oversold
	tp_long, tp_short
	sl_long, sl_short

	WORST INDIVIDUAL:
	{output_worst}
	{population[-1].genes}
	''')

	the_bests.append( best )

# BEST RESULT FROM EVOLUTION
print(
	'*** *** *** *** *** BETTER RESULT OVERALL *** *** *** *** *** ',
	pd.DataFrame.from_dict(
		max( the_bests, key= lambda x: x['profit_after_fees'] ),
		orient='index')
)
