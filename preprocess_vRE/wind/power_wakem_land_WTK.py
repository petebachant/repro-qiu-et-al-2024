import numpy as np
import pandas as pd
import sys
import xarray as xr
sys.path.append('/net/eofe-netapp-nfs/home/lyqiu/functions/python')
from myfunctions import *
from cdo import *
cdo=Cdo()

mdl="WTK"
inputdir = f"/nobackup1/lyqiu/WindUncertainty/Data/{mdl}/"
outputdir = f"/nobackup1/lyqiu/NetLoad/WindData/{mdl}/"
cases=["onshore"]
Nt=64

# get iy and im from command line
iy=int(sys.argv[1])
im=int(sys.argv[2])

for ca in cases:
    if ca!="offshore":
        Nt = 64
        lookupt = np.genfromtxt(
            f"/nobackup1/lyqiu/wake_model/power_lookup_nt{Nt}_sum_IEA_3.4MW_130_RWT.dat", delimiter=',')
        wsh = 100
        ex = (110/wsh)**(1/7)
        wtmdl = "IEA_3.4MW_130_RWT"
        minws = 3
        maxws = 25
    else:
        Nt = 100
        lookupt = np.genfromtxt(
            f"/nobackup1/lyqiu/wake_model/power_lookup_nt{Nt}_sum_IEA_10MW_198_RWT.dat", delimiter=',')
        wsh = 100
        ex = ((119/wsh)**(1/7))
        wtmdl = "IEA_10MW_198_RWT"
        minws = 4
        maxws = 25

    lookupt=lookupt/lookupt.max()
    for degree in [0.06]:
        degrees = f'{degree:0.2f}'
        maskfilen = f"/nobackup1/lyqiu/NetLoad/map/ISNE_74.5W_40N_{ca}_{degrees}.nc"
        maskd=read_netcdf(maskfilen,"mask").squeeze()
        u_interpolated=cdo.remapbil(maskfilen,input="-mulc,%f %s/%dm/%s_u%d_%d_%02d.nc"%(ex,inputdir, wsh,mdl, wsh, iy, im),returnXArray="u")
        v_interpolated = cdo.remapbil(maskfilen, input="-mulc,%f %s/%dm/%s_v%d_%d_%02d.nc" % (
            ex, inputdir, wsh, mdl, wsh, iy, im), returnXArray="v")
        u_interpolated = u_interpolated*maskd
        v_interpolated = v_interpolated*maskd
        ws, wd = wswd_from_uv(u_interpolated, v_interpolated)
        condition1 = (ws < minws) | (ws > maxws)
        ws = xr.where(condition1, np.nan, ws)
        (nt,nlat,nlon)=ws.shape
        wd_index=np.round(wd)
        wd_index=wd_index.where(wd_index<360,wd_index-360)
        tmp=np.round(ws,2)
        tmp = (tmp-minws)/0.01


        ws_index=tmp;
        wd_index=wd_index.astype(int);
        ws_index=ws_index.astype(int);
        ws_index=ws_index.where(ws_index>=0,0)
        POWERS_3d = ws
        for ilon in range(nlon):
            for ilat in range(nlat):
                if maskd[ilat,ilon]==1:
                    print([ilon,ilat])
                    for it in range(nt):
                        if ~(ws_index.data[it,ilat,ilon]==0):
                            POWERS_3d[it,ilat,ilon]=lookupt[wd_index[it,ilat,ilon],ws_index[it,ilat,ilon]]
                        else:
                            POWERS_3d[it,ilat,ilon]=0.
                else:
                    POWERS_3d[:,ilat,ilon]=-999.
        POWERS_3d.to_netcdf("%s/%s_wakecf%d_%s_%d_%02d_%.2f.nc"%(outputdir,mdl,Nt,ca,iy,im,degree))
        


