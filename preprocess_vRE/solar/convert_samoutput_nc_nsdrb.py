import pandas as pd
import xarray as xr
import os
from cdo import *
cdo=Cdo()
# Path to the directory containing CSV files
def generate_date_range_without_leap_day(start, end, freq):
    date_range = pd.date_range(start=start, end=end, freq=freq)
    return [date for date in date_range if date.month != 2 or date.day != 29]
nameplate=200.72*1000 #kW
# List to store DataArrays
casename='case_PVwatts_farm_nofinancial'
for yr in range(2007,2008):
    csv_directory = f'/nobackup1/lyqiu/NetLoad/SolarData/NSRDB/output/PVwatts/csv/{yr}'
    nc_directory = f'/nobackup1/lyqiu/NetLoad/SolarData/NSRDB/output/PVwatts/netcdf/'
    filen = f'{nc_directory}/NSRDB_{yr}_SAM_local_4km_cf.nc'
    data_arrays = []
    if not os.path.exists(filen):
        files=os.listdir(csv_directory)
        files=sorted(files)
        for filename in files:
            if filename.endswith('.csv'):
                file_path = os.path.join(csv_directory, filename)
                dnames=filename.split('_')
                time=generate_date_range_without_leap_day(start=f'{yr}-01-01 00:00:00',end=f'{yr}-12-31 23:00:00',freq='H')
                pvfile=f'{csv_directory}/{dnames[0]}_{dnames[1]}_{dnames[2]}_SAM.csv'
                df_pv = pd.read_csv(pvfile,header=None)
                # Extract data from DataFrame and create DataArray
                data_array = xr.DataArray(df_pv[0], dims=['time'], coords={'time': time})
                # Add latitude and longitude as coordinates
                # Assuming latitude is the same for all rows in the CSV
                latitude = float(dnames[0])
                # Assuming longitude is the same for all rows in the CSV
                longitude = float(dnames[1])
                data_array = data_array.assign_coords(latitude=latitude, longitude=longitude)
                data_arrays.append(data_array)
        # Combine DataArrays into a single Dataset
        combined_dataset = xr.concat(data_arrays, dim='location')
        combined_dataset = combined_dataset.transpose('time', 'location', ...)
        combined_dataset=combined_dataset.rename('cf')
        combined_dataset=combined_dataset/nameplate #KW to MW
        combined_dataset=combined_dataset.assign_attrs({'units':'cf','description':'Solar power output from SAM PVwatts model,nameplate:200.72, NSRDB input data','long_name':'system_power_generated','standard_name':'gen'})
        combined_dataset.to_netcdf(filen) 
        gridfile = "/nobackup1/lyqiu/NetLoad/script/solar/grid_ISNE_NSRDB_SAM"
        if not os.path.exists(gridfile):
            line1 = "gridtype=unstructured"
            nloc = combined_dataset.shape[1]
            line2 = "gridsize=%d" % (nloc)
            line3 = "yvals="
            line4 = "xvals="
            for ii in range(nloc):
                line3 = line3+"%.2f " % (combined_dataset['latitude'][ii])
                line4 = line4+"%.2f " % (combined_dataset['longitude'][ii])
            with open(gridfile, "w") as file:
                file.write(line1+"\n")
                file.write(line2+"\n")
                file.write(line3+"\n")
                file.write(line4+"\n")  
            
        #cdo.ifthen(f'/nobackup1/lyqiu/NetLoad/map/ISNE_74.5W_40N_onshore_0.04.nc',input=f'-remapnn,/nobackup1/lyqiu/NetLoad/map/ISNE_74.5W_40N_onshore_0.04.nc -setgrid,/nobackup1/lyqiu/NetLoad/script/solar/grid_ISNE_NSRDB_SAM {filen}', output=f'{nc_directory}/NSRDB_{yr}_SAM_local_0.04.nc', options='-b f32')


