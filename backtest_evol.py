from 	GenAlgo 	import 	Population
from 	strategies 	import 	BBStrategy
import 	pandas 		as 		pd
from 	utils 		import 	klinesFilter
import 	re

# IMPORT DATA SOURCES
pathFile 		= '/home/llagask/trading/binance-api-samchardyWrap/data/1h/binance-BTCUSDT-1h.csv'
df 				= pd.read_csv(pathFile)
df 				= klinesFilter(df,tf='1h')
df              = df.iloc[-6000:-1]
start_date 		= df.index[0]
end_date 		= df.index[-1]
pairNamePattern = re.compile('[A-Z]{6,}')
symbol 			= pairNamePattern.search(pathFile).group()
timeframe 		= '1h'

genes_candidates = [
	'bb_len',
	'n_std',
	'rsi_len',
	'rsi_overbought',
	'rsi_oversold',
	'tp_long',
	'tp_short',
	'sl_long',
	'sl_short'
]
tpLong              = lambda n : (n/100)+1
tpShort             = lambda n : (100-n)/100
slLong              = lambda n : (100-n)/100
slShort             = lambda n : (n/100)+1

# ALGORITHM SETUP
generation_size				= 25
n_genes						= 9
gene_ranges 				= [
							(40, 51),	# bb_len
							(18, 21),	# n_std
							(20, 31),	# rsi_len
							(60, 75),	# rsi_overbought
							(35, 50),	# rsi_oversold
							(5,10),		# tp_long
							(5,10),		# tp_short
							(2,5),		# sl_long
							(2,5)		# sl_short
]
n_best 						= 5
mutation_rate 				= 0.1

# *** *** *** *** *** *** *** ***
number_of_generations 		= 100
# *** *** *** *** *** *** *** ***

# DISCRETIONARY PARAMETERS
initial_balance 			= 1000
entry_amount_percentage 	= 0.05
leverage 					= 5
trailing_stop_loss 			= True
bullMarket					= False
bearMarket					= True

P = Population(
	generation_size 		= generation_size,
	n_genes 				= n_genes,
	gene_ranges 			= gene_ranges,
	n_best 					= n_best,
	mutation_rate 			= mutation_rate,

	initial_balance 		= initial_balance,
	leverage 				= leverage,
	trailing_stop_loss 		= trailing_stop_loss,
	entry_amount_percentage = entry_amount_percentage,
	bullMarket				= bullMarket,
	bearMarket				= bearMarket
	)

population 					= P.population

# *** *** ----- ----- START ITERATION ----- ----- *** ***

print(f'''GENETIC ALGORITHM TO OPTIMIZE QUANT STRATEGY
BOLLINGER BANDS - RSI
SYMBOL: {symbol} ~ TIMEFRAME: {timeframe}''')

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
			tp_long			= tpLong  (genes[5]),
			tp_short		= tpShort (genes[6]),
			sl_long			= slLong  (genes[7]),
			sl_short		= slShort (genes[8])
		)
	P.crossover()
	P.mutation()
	population = sorted(
		population,
			key = lambda individual: individual.backtester.return_results(
																		symbol 		= symbol,
																		start_date 	= start_date,
																		end_date 	= end_date,
			)['fitness_function'], reverse = True
	)

	best = population[0].backtester.return_results(
												symbol		= symbol,
												start_date 	= start_date,
												end_date 	= end_date
	)
	worst 			= population[-1].backtester.return_results(
															symbol 		= symbol,
															start_date 	= start_date,
															end_date 	= end_date
	)

	best['genes***']				= population[0].genes
	worst['genes'] 					= population[-1].genes

	output_best 					= pd.DataFrame.from_dict(best, orient='index')
	output_worst 					= pd.DataFrame.from_dict(worst, orient='index')

	# *** -------------------- PERSISTENCE ----------------------***

	persistOnMongo 	= False

	# *** -------------------- PERSISTENCE ----------------------***

	print(f'''
	GENERATION: {x}
	_____________________________________________
	BEST INDIVIDUAL:
	{output_best}

	WORST INDIVIDUAL:
	{output_worst}''')

	the_bests.append( best )

	# *** *** END OF CYCLE (generations) *** ***


better1 = max( the_bests,key = lambda x: x['profit_after_fees'] )
better2 = max( the_bests, key = lambda x: x['fitness_function'] )

better1['initial_balance'] 			= initial_balance
better1['entry_amount_percentage'] 	= entry_amount_percentage
better1['leverage'] 				= leverage
better1['trailing_stop_loss'] 		= trailing_stop_loss
better1['Bull market']		 		= bullMarket
better1['Bear market']		 		= bearMarket

# BEST RESULT FROM EVOLUTION
print(f'''
*************** BETTER RESULTS OVERALL ***************
'profit_after_fees':__________________________________
{pd.DataFrame.from_dict(
						max( the_bests, key = lambda x: x['profit_after_fees'] ),
						orient='index'
)
}

'fitness_function':___________________________________
{pd.DataFrame.from_dict(
						max( the_bests, key = lambda x: x['fitness_function'] ),
						orient='index'
)
}

{
	genes_candidates
}

*** END ***
''')

if persistOnMongo:
	import pymongo
	from pymongo import MongoClient
	from datetime import datetime

	# PERSISTENCE
	client 		= MongoClient()
	db 			= client.backtest
	collection 	= db.semillitasBest
	# document 	= best
	documents 	= the_bests
	# collection.insert_one( document )

	result 		= collection.insert_many( documents )
	result.inserted_ids

