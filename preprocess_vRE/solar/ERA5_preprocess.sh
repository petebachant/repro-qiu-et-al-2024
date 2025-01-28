#!/bin/bash
#organize the file into the year of local time (but the time is still UTC)
idir=/nobackup1/lyqiu/NetLoad/SolarData/ERA5/ssrd_fdir_wind_sp_t2m/
cdo -b f32 shifttime,-5hour -mergetime ${idir}/????.nc ${idir}/ERA5_input_localized.nc
cdo splityear ${idir}/ERA5_input_localized.nc ${idir}/ERA5_input_localized_
for iy in {2007..2014};do
cdo shifttime,5hour ${idir}/ERA5_input_localized_${iy}.nc ${idir}/ERA5_input_localized_${iy}_UTC.nc
done
rm ${idir}/ERA5_input_localized_????.nc ${idir}/ERA5_input_localized.nc

