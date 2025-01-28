import h5pyd
import numpy as np
import pandas as pd

f = h5pyd.File("/nrel/nsrdb/v3/nsrdb_2012.h5", 'r')
meta = pd.DataFrame(f['meta'][...])
states_b=[b'Maine',b'Massachusetts',b'Connecticut',b'New Hampshire',b'Rhode Island',b'Vermont']
states_f=['Maine','Massachusetts','Connecticut','New Hampshire','Rhode Island','Vermont']
for ist in range(len(states_b)):
data = meta.loc[meta['state'] == states_b[ist]] # Note .h5 saves strings as bit-strings
latlon=data[['latitude','longitude']]
latlon.to_csv(f'{states_f[ist]}_lonlat.csv')
