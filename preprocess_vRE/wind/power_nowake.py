import numpy as np
import pandas as pd
import os
import sys
import xarray as xr
sys.path.append('../functions.py')
from functions import uv2wswd,read_netcdf
from cdo import *
cdo=Cdo()
cases=["onshore"]
mdls=["High","Low"]
#High is WTK and Low is ERA5
hdir = "/pool001/lyqiu/Siting_Optimization/NE_2024/"
sy=2007
ey=2013
degrees=[1.00,2.00] #OR

def get_power(data, lookupt):
    lookupt['CF']=lookupt['ElectricalPower']/lookupt['ElectricalPower'].max()
    minws=lookupt['WindSpeed'][0]
    maxws=lookupt['WindSpeed'][len(lookupt)-1]
    datac=data
    condition1 = (data < minws) | (data>maxws)
    data = xr.where(condition1, np.nan, data)
    tmp=np.interp(data,lookupt['WindSpeed'], lookupt['CF'])
    datac.values=tmp
    datac=datac.rename('cf')
    #set values outside 0-1 to 0
    condition2 = (datac < 0) | (datac>1)
    datac = xr.where(condition2, 0, datac)
    #set nan to 0
    datac = xr.where(datac.isnull(), 0, datac)
    return datac

for ca in cases:
    if ca=="onshore":
        lookupt=pd.read_csv(f"{hdir}/Parameters/IEA_3.4MW_130_RWT.csv", delimiter=',')
        height_WS=100 #height of wind speed of weather dta
        height_WT=110
        ex = (height_WT/height_WS)**(1/7)
        WT_name='IEA_3.4MW_130'
    for degree in degrees: #OR
        maskfilen = "%s/maskfiles/ISNE_grids/ISNE_%.2f.nc" % (
            hdir, degree)
        maskd = read_netcdf(maskfilen, "mask").squeeze()
        for mdl in mdls:
            inputdir = f"{hdir}/Meteorological_Data/{mdl}/Wind/"
            outputdir = f"{hdir}/CF_Data/{mdl}/Wind/"
            if mdl=="High":
                for iy in range(sy,ey+1):
                    for im in range(1,13):
                        data = cdo.remapbil(
                            maskfilen, input="-mulc,%f %s/ws%d/ws%d_%d_%02d.nc" % (ex, inputdir, height_WS, height_WS, iy, im),
                            returnXArray='ws')
                        datac=get_power(data,lookupt)
                        datac=datac*maskd
                        datac.to_netcdf("%s/nowake/cf_Wind_%d_%02d_%.2f.nc"%(outputdir,iy,im,degree))
                    
                    cdo.ifthen(input="%s -setname,cf -mergetime %s/nowake/cf_Wind_%d_??_%.2f" %
                               (maskfilen,outputdir,iy,degree),
                               output="%s/nowake/cf_Wind_%d_%.2f" %
                               (outputdir,iy,degree),options='-b f32')
                    cdo.cleanTempDir()
                    os.system("%s/nowake/cf_Wind_%d_??_%.2f" %
                              (maskfilen, outputdir, iy, degree))
            else:
                for iy in range(sy,ey+1):
                    # mask points close to coastline (less than 50% land in the grid)
                    datafile = f"{inputdir}/ws{height_WS}/ws{height_WS}_{iy}_masked.nc"
                    if not os.path.exists(datafile):
                        if os.path.exists(f"{inputdir}/ws{height_WS}/ws{height_WS}_{iy}.nc"):
                            cdo.ifthen(f"{inputdir}/ERA5_mask_ge50.nc", input=f"{inputdir}/ws{height_WS}/ws{height_WS}_{iy}.nc",output=datafile)
                        else:
                            u = read_netcdf(f"{inputdir}/uv{height_WS}/u{height_WS}_{sy}_{ey}.nc", "u")
                            v = read_netcdf(f"{inputdir}/uv{height_WS}/v{height_WS}_{sy}_{ey}.nc", "v")
                            ws,wd=uv2wswd(u,v)
                            ws.sel(time=(ws.time.dt.year==iy)).to_netcdf(f"{inputdir}/ws{height_WS}/ws{height_WS}_{iy}.nc")
                            wd.sel(time=(wd.time.dt.year == iy)).to_netcdf(f"{inputdir}/wd{height_WS}/wd{height_WS}_{iy}.nc")
                    data = cdo.remapbil(maskfilen, input="-mulc,%f %s" % (ex, datafile),returnXArray='ws')
                    datac=get_power(data,lookupt)
                    datac =datac*maskd
                    datac.to_netcdf(f"tmp.nc")
                    cdo.ifthen(input="%s -setmisstoc,0 -setvrange,0,1 -setname,cf tmp.nc"%(maskfilen),
                        output="%s/nowake/cf_Wind_%d_%.2f" %(outputdir, iy, degree), options='-b f32')
                    cdo.cleanTempDir()
            
    

