import pandas as pd
import xarray as xr
import os

# Path to the directory containing CSV files

# List to store DataArrays

for yr in range(2011,2014):
    csv_directory = f'/nobackup1/lyqiu/NetLoad/SolarData/NSRDB/input/csv/{yr}/'
    for var in ['DHI','DNI','GHI']:
        filen= f'/nobackup1/lyqiu/NetLoad/SolarData/NSRDB/input/netcdf/{var}_{yr}.nc'
        data_arrays = []
        if not os.path.exists(filen):
            # Loop through CSV files in the directory
            files=os.listdir(csv_directory)
            files=sorted(files)
            for filename in files:
                if filename.endswith('.csv'):
                    file_path = os.path.join(csv_directory, filename)
                    # Read CSV file into a pandas DataFrame
                    df = pd.read_csv(file_path,header=2)
                    month_str = df['Month'].apply(lambda x: str(x).zfill(2))
                    day_str = df['Day'].apply(lambda x: str(x).zfill(2))
                    hour_str = df['Hour'].apply(lambda x: str(x).zfill(2))
                    minute_str = df['Minute'].apply(lambda x: str(x).zfill(2))
                    # Concatenate the components
                    time_str = df['Year'].astype(str) + month_str + day_str + hour_str + minute_str
                    # Convert the concatenated string to datetime
                    time = pd.to_datetime(time_str, format='%Y%m%d%H%M')
                    # Extract data from DataFrame and create DataArray
                    data_array = xr.DataArray(df[var], dims=['time'], coords={'time': time})
                    # Add latitude and longitude as coordinates
                    latitude = float(filename.split('_')[1])  # Assuming latitude is the same for all rows in the CSV
                    longitude = float(filename.split('_')[2])  # Assuming longitude is the same for all rows in the CSV
                    data_array = data_array.assign_coords(latitude=latitude, longitude=longitude)
                    # Add the DataArray to the list
                    data_arrays.append(data_array)

            # Combine DataArrays into a single Dataset
            combined_dataset = xr.concat(data_arrays, dim='location')
            combined_dataset = combined_dataset.transpose('time', 'location', ...)
            combined_dataset.to_netcdf(filen) 
            #cdo.ifthen(input=f'US-ISNE_4km.nc -remapnn,grid_ISNE_NSRDB_remap -setgrid,grid_ISNE_NSRDB {filen}',output=f'/nobackup1/lyqiu/NetLoad/SolarData/NSRDB/input/netcdf/{yr}_remap.nc',options='-b f32')


