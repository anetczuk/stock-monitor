#!/usr/bin/env python3
#
#
#

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tic


fig = plt.figure()

x = np.arange(100)
y = 3. * np.sin( x * 2. * np.pi / 100. )

plt.subplots_adjust( hspace=0.001 )

for i in range(5):
    pos = 511 + i
    ax = plt.subplot( pos )
    plt.plot( x, y )
    nloc = tic.MaxNLocator(3)
    ax.yaxis.set_major_locator(nloc)
    ax.set_xticklabels(())
    ax.title.set_visible(False)

plt.show()
