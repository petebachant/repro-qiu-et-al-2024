import pandas as pd
import xarray as xr
import os
from cdo import *
cdo = Cdo()

casename='PVwatts'

nc_directory = f'/nobackup1/lyqiu/NetLoad/SolarData/ERA5/output/PVwatts/netcdf/'
nc_ori_directory = f'/nobackup1/lyqiu/NetLoad/SolarData/ERA5/input/netcdf/'
filen= f'{nc_directory}/ERA5_2007_2013_SAMcf_local.nc'
data = cdo.delete('month=2,day=29', input=f'{nc_ori_directory}/ERA5_GHI_2007_2013_local.nc', returnXArray='GHI')
data=data.rename('cf')
print(data.shape)
data=data.assign_attrs({'units':'capacity factor','description':'Solar power output from SAM PVwatts model, nameplate=200.72MW ERA5 input data','long_name':'system_power_generated','standard_name':'gen'})
nameplate=200.72*1000 #kW
sy=2007
ey=2013
for iy in range(ey-sy+1):
    yr=iy+sy
    csv_directory = f'/nobackup1/lyqiu/NetLoad/SolarData/ERA5/output/PVwatts/csv/{yr}'
    for ilat in range(len(data.latitude)):
        lat="%.02f"%(data.latitude[ilat])
        for ilon in range(len(data.longitude)):
            lon="%.02f"%(data.longitude[ilon])
            csvname=f'{csv_directory}/ERA5_{lat}_{lon}_{yr}_SAM.csv'
            if os.path.exists(csvname):
                asf=pd.read_csv(csvname,header=None)[0].values
                data.loc[dict(time=slice(f'{yr}-01-01',f'{yr}-12-31'),latitude=lat,longitude=lon)]=asf/nameplate
            else:
                data.loc[:, lat, lon] = -32767.

data.to_netcdf(filen) ##UTC time

