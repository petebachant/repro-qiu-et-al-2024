# ##library setting##
import numpy as np
import xarray as xr
import pandas as pd
import pvlib
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="xarray")

idir="/nobackup1/lyqiu/NetLoad/SolarData/ERA5/input/netcdf"
odir="/nobackup1/lyqiu/NetLoad/SolarData/ERA5/input/csv/"
sy=2007
ey=2013
#timezone
lct=-5 #eastern us
altitude=xr.open_dataset(f'{idir}/era5_height.nc')['z'].squeeze() #from ERA5 geopotentail 
mask=xr.open_dataset(f'/nobackup1/lyqiu/NetLoad/map/ISNE_74.5W_40N_onshore_0.25_inv.nc')['mask'].squeeze() #from ERA5 lsm, taking >=0.85 as land
# mask['longitude']=mask['longitude']-360 #shift the longitude to -180~180
altitude['longitude']=altitude['longitude']-360

for iy in range(sy,ey+1):
    ds=xr.open_dataset(f'{idir}/ERA5_input_{iy}_UTC.nc') # each file should contain 1 year of data in local time but UTC time (i.e. 01-01 05:00:00 to 01-01 04:00:00)
    #GHI
    ds_new=xr.Dataset()
    ds_new['GHI']=(ds.ssrd / 3600.0).assign_attrs(units="W/m^2", long_name="global horizontal irradiation") #J/M2 to W/M2
    ds_new['GHI'] = ds_new['GHI'].where(ds_new['GHI'] > 0,ds_new['GHI'], 0)
    ds_new["GHI"] = ds_new["GHI"].fillna(0)
        #DHI
    dirhi = (ds.fdir / 3600.0).assign_attrs(units="W/m^2")
    ds_new['DHI'] = (ds_new['GHI'] - dirhi).assign_attrs(units="W/m^2",long_name="Diffuse Horizontal Irradiance")
    ds_new['DHI'] = ds_new['DHI'].where(ds_new['DHI'] > 0,ds_new['DHI'], 0)
    ds_new["DHI"] = ds_new["DHI"].fillna(0)
    ds_new['DNI'] = xr.DataArray(np.zeros(ds_new['GHI'].shape), coords=ds_new['GHI'].coords, dims=ds_new['GHI'].dims)
    ds_new['Temperature']=ds['t2m']-273.15
    ds_new["Dew Point"] = ds['d2m'] - 273.15
    ds_new['Pressure']=ds['sp']
    times = pd.to_datetime(ds_new['GHI'].time)
    lats=ds_new['GHI']['latitude'].values
    lons=ds_new['GHI']['longitude'].values
    ds_new['DNI'] = xr.DataArray(np.zeros(ds_new['GHI'].shape), coords=ds_new['GHI'].coords, dims=ds_new['GHI'].dims)
    ds_new["Wind Speed"] = np.sqrt(ds["u10"] ** 2 + ds["v10"] ** 2).assign_attrs(units=ds["u10"].attrs["units"], long_name="10 metre wind speed")
    avg_pressure=ds_new['Pressure'].mean(dim='time').squeeze()
    avg_temperature=ds_new['Temperature'].mean(dim='time').squeeze()
    for i in range(lats.size):
        for j in range(lons.size):
            lat = lats[i]
            lon=lons[j]
            alt=altitude[i,j].values
            # time : pandas.DatetimeIndex Localized or UTC.altitude : float
            spa = pvlib.solarposition.spa_python(time=times, latitude=lat, longitude=lon, altitude=alt,pressure=avg_pressure[i, j].values, temperature=avg_temperature[i, j].values)
            ds_new['DNI'][:, i, j] = pvlib.irradiance.dni(ghi=ds_new['GHI'][:, i, j].data, dhi=ds_new['DHI'][:, i, j].data, zenith=spa["zenith"], zenith_threshold_for_zero_dni=88.0)

    #ds_new['DNI'] = xr.where(ds_new['DNI'] > 0,ds_new['DNI'], 0)
    ds_new["DNI"] = ds_new["DNI"].fillna(0)
    ds_new["DNI"]=xr.where(ds_new["DNI"]<=1367,ds_new["DNI"],1367)
    ds_new["DNI"] = ds_new['DNI'].assign_attrs(units="W/m^2", long_name="direct irradiation")  # J/M2 to W/M2
    ds_new['DNI'].to_netcdf(f'{idir}/ERA5_DNI_{iy}_UTC.nc')
    ds_new['DHI'].to_netcdf(f'{idir}/ERA5_DHI_{iy}_UTC.nc')
    lid=1
    for i in range(lats.size):
        for j in range(lons.size):
            if mask[i,j]==1:
                lat = lats[i]
                lon = lons[j]
                alt = altitude[i, j].values
                # time : pandas.DatetimeIndex Localized or UTC.altitude : float
                da=ds_new.sel(latitude=lat,longitude=lon)
                dd = da.to_dataframe()
                # dd=da.to_dataframe().reset_index()
                # dd.set_index(["time"], inplace=True)
                dd.sort_index(inplace=True)
                dd = dd.tz_localize("UTC", level=0).tz_convert("US/Eastern")
                dd['Year'] = dd.index.year
                dd['Month'] = dd.index.month
                dd['Day'] = dd.index.day
                dd['Hour'] = dd.index.hour
                dd['Minute'] = '0'
                dd["Pressure"] = dd["Pressure"]/100
                dd = dd[['Year', 'Month', 'Day', 'Hour', 'Minute', 'DNI', 'DHI',
                            'GHI', 'Dew Point', 'Temperature', 'Pressure', 'Wind Speed']]
                dd = dd.reset_index().drop(columns=['time'])
                lonstr = '%.2f' % (lon)
                latstr = '%.2f' % (lat)
                csvname = f"{odir}/{iy}/ERA5_{lid}_{latstr}_{lonstr}_{iy}.csv"
                dd.to_csv(csvname, index=False)
                line1 = "Source,Location ID,Latitude,Longitude,Time Zone,Elevation,Local Time Zone,Dew Point Units,DHI Units,DNI Units,GHI Units,Solar Zenith Angle Units,Temperature Units,Pressure Units,Wind Speed Units"
                line2 = f"ERA5,{lid},{lat},{lon},{lct},{alt},{lct},c,w/m2,w/m2,w/m2,Degree,c,mbar,m/s"
                with open(csvname, "r") as file:
                    original_contents = file.read()
                with open(csvname, "w") as file:
                    # Write new lines followed by the original contents
                    file.write(f"{line1}\n{line2}\n" + original_contents)
                lid += 1

    
