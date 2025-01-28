from PySAM.PySSC import PySSC
import csv
import pandas as pd
import os
import multiprocessing as mp
from functools import partial
import glob

def sam(index,idir,iy,odir):
	ssc.module_exec_set_print(0)
	data = ssc.data_create()
	#read data
	ifile = glob.glob(f'{idir}/{index}_*.csv')[0]
	lat = ifile.split('_')[2]
	lon = ifile.split('_')[3]
	outputn = f'{odir}/{iy}/{lat}_{lon}_{iy}_SAM.csv'
	if not os.path.exists(outputn):
		ssc.data_set_string( data, b'solar_resource_file', ifile.encode('utf-8'));
		albedo =[ 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001 ];
		ssc.data_set_array( data, b'albedo',  albedo);
		ssc.data_set_number( data, b'use_wf_albedo', 1 )
		ssc.data_set_number( data, b'system_capacity', 200000.72177199999 )
		ssc.data_set_number( data, b'module_type', 0 )
		ssc.data_set_number( data, b'dc_ac_ratio', 1.1499999999999999 )
		ssc.data_set_number( data, b'bifaciality', 0 )
		ssc.data_set_number( data, b'array_type', 2 )
		ssc.data_set_number( data, b'tilt', 42 )
		ssc.data_set_number( data, b'azimuth', 180 )
		ssc.data_set_number( data, b'gcr', 0.29999999999999999 )
		soiling =[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ];
		ssc.data_set_array( data, b'soiling',  soiling);
		ssc.data_set_number( data, b'losses', 14.075660688264469 )
		ssc.data_set_number( data, b'en_snowloss', 0 )
		ssc.data_set_number( data, b'inv_eff', 96 )
		ssc.data_set_number( data, b'batt_simple_enable', 0 )
		ssc.data_set_number( data, b'adjust:constant', 0 )
		ssc.data_set_array_from_csv( data, b'grid_curtailment', b'grid_curtailment.csv');
		ssc.data_set_number( data, b'enable_interconnection_limit', 0 )
		ssc.data_set_number( data, b'grid_interconnection_limit_kwac', 100000 )
		module = ssc.module_create(b'pvwattsv8')	
		ssc.module_exec_set_print( 0 );
		if ssc.module_exec(module, data) == 0:
			print ('pvwattsv8 simulation error')
			idx = 1
			msg = ssc.module_log(module, 0)
			while (msg != None):
				print ('	: ' + msg.decode("utf - 8"))
				msg = ssc.module_log(module, idx)
				idx = idx + 1
			SystemExit( "Simulation Error" );
		ssc.module_free(module)
		module = ssc.module_create(b'grid')	
		ssc.module_exec_set_print( 0 );
		if ssc.module_exec(module, data) == 0:
			print ('grid simulation error')
			idx = 1
			msg = ssc.module_log(module, 0)
			while (msg != None):
				print ('	: ' + msg.decode("utf - 8"))
				msg = ssc.module_log(module, idx)
				idx = idx + 1
			SystemExit( "Simulation Error" );
		ssc.module_free(module)

		datac=[]
		da=ssc.data_get_array(data, b'gen')
		datac = [[num] for num in da]
		with open(outputn, mode='w', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerows(datac)	

   
ssc = PySSC()
sy=2007
ey=2013
hdir = '/pool001/lyqiu/Siting_Optimization/NE_2024/'

states=['Rhode_Island', 'Maine', 'Massachusetts', 'Connecticut', 'New_Hampshire', 'Vermont']


mdls=["High","Low"]
for mdl in mdls:
	if mdl=="High":
		indexes_df = pd.DataFrame()
		for state in states:
			df = pd.read_csv(
				f'{hdir}/scripts/step1_vRE/solar/points_NSRDB/{state}_lonlat.csv', index_col=0)
			indexes_df = pd.concat([indexes_df, df])	
		indexes = indexes_df.reset_index()['index'].values
	else:
		indexes = range(1, 308)

	for iy in range(sy,ey+1):
		idir = f'{hdir}/Meteorological_Data/{mdl}/Solar/{iy}/'
		odir = f'{hdir}/CF_Data/{mdl}/Solar/{iy}/'
		if __name__ == '__main__':
			pool = mp.Pool(mp.cpu_count())
			func = partial(sam,idir=idir,iy=iy,odir=odir)
			results = pool.map(func, indexes)
			pool.close()
		
