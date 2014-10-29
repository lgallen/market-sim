# python marketsim.py 1000000 orders.csv values.csv
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import csv
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Input starting value and benchmark here
cash = 1000000
benchmark = ["$SPX"]

# read in order data from orders.csv
cnames=["year","month","day","symbol","order","quantity"]
odf = pd.read_csv("orders.csv",index_col=False, names=cnames)

# create list of order dates
order_dates = []
ncols = odf.shape[0]
for i in range(0,ncols):
    order_dates.append(dt.datetime(odf['year'][i],odf['month'][i],odf['day'][i]))

# find start and end date
dt_start = min(order_dates)
dt_end = max(order_dates)

# create list of symbols
ls_symbols = list(set(odf["symbol"]))

# pull in data from yahoo
dt_timeofday = dt.timedelta(hours=16)
ldt_timestamps = du.getNYSEdays(dt_start, dt_end+dt.timedelta(days=1), dt_timeofday)
days = len(ldt_timestamps)
c_dataobj = da.DataAccess('Yahoo')
ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
d_data = dict(zip(ls_keys, ldf_data))

# initialize values dataframe with all zeros
val_names = np.concatenate((["dates","cash"],ls_symbols,["value"]),1)
zero_data=np.zeros(shape=(len(ldt_timestamps ),len(val_names)))
values=pd.DataFrame(data=zero_data, columns=val_names)

# fill dates column and initialize cash column
values['dates']=ldt_timestamps
values['cash']=cash

# get day each order occurred by nyse days
num_od = len (order_dates)
nyse_day = []
for i in range(0,num_od):
    nyse_day.append(len(du.getNYSEdays(order_dates[0],order_dates[i]))-1)

odf['nyse_day']=nyse_day

odf = odf.sort('nyse_day')


# update cash value and stock amount for each day 
for i in range(0,days-1):
    values['cash'][i+1]=values['cash'][i] 
    values.ix[i+1,ls_symbols]=values.ix[i,ls_symbols]
    for j in range(0,num_od):
        if odf['nyse_day'][j] == i:
            symbol_pos = ls_symbols.index(odf['symbol'][j])
            order_val = d_data['close'].values[i,symbol_pos]*odf['quantity'][j]
            if odf['order'][j] == 'Sell':
                # increase cash value by appropriate amount
                values['cash'][i+1]=values['cash'][i+1] + order_val
                # now replace sold stock by subtracting quantity of sold stock
                values.ix[i+1,symbol_pos+2] = values.ix[i,symbol_pos+2] - odf['quantity'][j]                
            elif odf['order'][j] == 'Buy':
                # repeat selling strategy, modified slightly for buying
                values['cash'][i+1]=values['cash'][i+1] - order_val
                values.ix[i+1,symbol_pos+2] = values.ix[i,symbol_pos+2] + odf['quantity'][j]
                
    

# update value column
for i in range(0, days):
    daily_val = 0 
    for j in range (0, len(ls_symbols)):
        symbol_val = d_data['close'].values[i,j]*values.ix[i,j+2]
        
        daily_val = daily_val+symbol_val
    values.ix[i,'value']=daily_val + values.ix[i,'cash']
    
# calculate fund statistics
total_return = values.ix[days-1,'value']/values.ix[0,'value']
final_value = values.ix[days-1,'value']

daily_return=tsu.returnize0(values.ix[0:days-1,'value'])
daily_return_mean = np.mean(daily_return)
daily_return_sd = np.std(daily_return)
sharpe_ratio_fund = (252**.5) * daily_return_mean / daily_return_sd

# pull in data for benchmark
ldf_data = c_dataobj.get_data(ldt_timestamps, benchmark, ls_keys)
d_data = dict(zip(ls_keys, ldf_data))


# calculate benchmark statistics
bench_values = d_data['close'].values
bench_total_return = bench_values[days-1]/bench_values[0]
bench_daily_return = tsu.returnize0(bench_values)
bench_return_mean = np.mean(bench_daily_return)
bench_return_sd = np.std(bench_daily_return)
sharpe_ratio_bench = (252**.5) * bench_return_mean / bench_return_sd

# output summary statistics
print "Details of the Performance of the portfolio :"
print ""   
print ("Data Range : "), (dt_start)," to " ,(dt_end)
print ""
print ("Final value of the portfolio is : "), (final_value)
print ""  
print ("Sharpe Ratio of Fund : "), (sharpe_ratio_fund)
print ("Sharpe Ratio of "),(benchmark[0]),(": ") , (sharpe_ratio_bench)
print ""   
print ("Total Return of Fund : "),(total_return)
print ("Total Return of") ,(benchmark[0]), (": ") , (bench_total_return[0])
print ""
print ("Standard Deviation of Fund : "), (daily_return_sd)
print ("Standard Deviation of"),(benchmark[0]),(": ") , (bench_return_sd)
print "" 
print ("Average Daily Return of Fund : ") ,(daily_return_mean)
print ("Average Daily Return of"),(benchmark[0]),(": "), (bench_return_mean)   