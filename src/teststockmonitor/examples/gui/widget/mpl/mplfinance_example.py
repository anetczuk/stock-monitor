#!/usr/bin/env python3
#
#
#

import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas
import random
import datetime
import numpy
import matplotlib

from typing import Dict


CANDLE_TYPE  = "candle"
CANDLE_STYLE = "default"


def get_date_format( xdata ):
    if len(xdata) > 1:
        timeSpan = xdata[-1] - xdata[0]
        if timeSpan > datetime.timedelta( days=2 ):
            ## long format
            return '%d-%m-%Y'
    return '%H:%M:%S'


start_date = datetime.datetime.now() - datetime.timedelta(days=20)
xdata = []

frame: Dict = { 'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': [] }

random.seed( 10 )

for i in range(0, 20):
    xdata.append( start_date )
    start_date += datetime.timedelta( days=random.choice( [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2] ) )
#     start_date += datetime.timedelta( days=1 )
    vopen = random.randrange( 10 )
    vclose = vopen + random.randint( -5, 5 )
    vmin = min( vopen, vclose ) - random.randrange( 3 )
    vmax = max( vopen, vclose ) + random.randrange( 3 )
    volume = random.randrange( 10 ) + 1

    frame[ "Open" ].append( vopen )
    frame[ "High" ].append( vclose )
    frame[ "Low" ].append( vmin )
    frame[ "Close" ].append( vmax )
    frame[ "Volume" ].append( volume )

dataframe = pandas.DataFrame( frame )
dataframe.index = pandas.DatetimeIndex( xdata )


fig = plt.figure()

fig.subplots_adjust( hspace=0.001 )

ax1 = fig.add_subplot( 2, 1, 1 )
ax2 = fig.add_subplot( 2, 1, 2 )

xdata = dataframe.index
date_format = get_date_format( xdata )

avg_dist_between_points = (xdata[-1] - xdata[0]) / float(len(xdata))
start_day = (xdata[0]  - 0.45 * avg_dist_between_points).timestamp() / (60 * 60 * 24)
end_day   = (xdata[-1] + 0.45 * avg_dist_between_points).timestamp() / (60 * 60 * 24)

data = mpf.plot(   dataframe,
                   type=CANDLE_TYPE,
                   style=CANDLE_STYLE,
                   #             volume=True,
                   ax=ax1,
                   volume=ax2,
                   datetime_format=date_format,
                   show_nontrading=True,
                   xlim=(start_day, end_day)
                   #             returnfig=True,
                   #            scale_padding=7.0,
                   #            **additionalParams
                   )


# fig.show()
plt.show()
