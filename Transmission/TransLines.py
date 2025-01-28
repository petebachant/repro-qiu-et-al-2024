# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 17:21:28 2024
estimate the cost of transmission line addition between new VRE assets and 
the existing network.

@author: Rahman Khorramfar
"""
import numpy as np;
import pandas as pd;
#%% setting and parameters
def run_trans(solar_df,wind_df):
    Zones = np.arange(1,7);
    Volt_lim = 115; #kV high-vol>115-230kV
    trans_line_cost = 3500; # $/MW/mile
    max_CF_solar = 1;
    max_CF_wind = 1;

    #%% 
    dfb = pd.read_csv('bus.csv')
    dfb = dfb[dfb['zone_id'].isin(Zones)]
    dfb = dfb[dfb['baseKV']>= Volt_lim];

    bus_id = dfb['bus_id'].to_numpy();
    dfb2s = pd.read_csv('bus2sub.csv');
    dfb2s = dfb2s[dfb2s['bus_id'].isin(bus_id)]
    sub_id = dfb2s['sub_id'].unique();

    dfs = pd.read_csv('sub.csv');
    dfs = dfs[dfs['sub_id'].isin(sub_id)];
    dfs = dfs.reset_index();
    dfs.to_csv('Existing_HV_nodes.csv')
    sub_loc = dfs[['lat','lon']].to_numpy();
    del dfb2s, bus_id,dfb,sub_id,Zones,Volt_lim;
    #%% distance from solar max
    for ic in range(2):
        if ic==0:
            df = solar_df;
        else:
            df = wind_df;
    
        min_dist_to_HV_node = np.zeros(len(df));
        cost_to_HV_node = np.zeros(len(df));
        exis = np.zeros((len(df),4));
        for i in range(len(df)):    
            loc = np.array(df[['lat','lon']].iloc[i])
            dists = np.linalg.norm(sub_loc-loc,axis=1)*60; # x60 to get distance in miles
            min_dist_to_HV_node[i] = np.min(dists);
            exis[i,0] = np.int16(np.argmin(dists));
            exis[i,1] = min_dist_to_HV_node[i];
            exis[i,2] = dfs['lat'].iloc[np.int16(exis[i,0])];
            exis[i,3] = dfs['lon'].iloc[np.int16(exis[i,0])];  
        cost_to_HV_node[i] = max_CF_solar*min_dist_to_HV_node[i]*df['capacity'].iloc[i]*trans_line_cost;
    df[['closest_existing_node','distance_mile','lat_exist_node','lon_exist_node']] = exis;
    df.to_csv('maximized_sub7yrs_ens1_ng_0_cc_0_wake_0_landr_0_wind-onshore0.06_solar-UPV0.14_WTK_solar-UPV_locations.csv')
    print(f'Total transmission line mileage: {np.sum(min_dist_to_HV_node)}')
    print(f'Total transmission expansion cost for maxSolar: {np.sum(cost_to_HV_node)}')

    
    
    
    





