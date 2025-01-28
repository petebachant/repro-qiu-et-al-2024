# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 15:18:12 2023

@author: Rahman Khorramfar
"""
from TransLines import run_trans
import numpy as np
import pandas as pd
import sys


def get_df_i(df, wake=None, land=None, cg=None, solarz=None, windz=None, ny=None, ensid=None):
    df = df.reset_index()
    df = df.set_index(['wake_allowd', 'landres_allowed', 'upper_bound_CCGT',
                      'cell_size_solar-UPV', 'cell_size_wind-onshore', 'num_yr', 'ens_id'])
    if wake is not None:
        dfa = df.iloc[df.index.get_level_values('wake_allowd') == wake]
    else:
        dfa = df
    if ny is not None:
        dfa = dfa.iloc[dfa.index.get_level_values('num_yr') == ny]
    if land is not None:
        dfa = dfa.iloc[dfa.index.get_level_values('landres_allowed') == land]
    if cg is not None:
        dfa = dfa.iloc[dfa.index.get_level_values('upper_bound_CCGT') == cg]
    if solarz is not None:
        dfa = dfa.iloc[dfa.index.get_level_values(
            'cell_size_solar-UPV') == solarz]
    if windz is not None:
        dfa = dfa.iloc[dfa.index.get_level_values(
            'cell_size_wind-onshore') == windz]
    if ensid is not None:
        dfa = dfa.iloc[dfa.index.get_level_values('ens_id') == ensid]
    
    return dfa['index'].values[0]

###########set up
Zones = np.arange(1, 7)
Volt_lim = 115  # kV high-vol>115-230kV
trans_line_cost = 3500  # $/MW/mile
max_CF_solar = 1
max_CF_wind = 1

dfb = pd.read_csv('bus.csv')
dfb = dfb[dfb['zone_id'].isin(Zones)]
dfb = dfb[dfb['baseKV'] >= Volt_lim]

bus_id = dfb['bus_id'].to_numpy()
dfb2s = pd.read_csv('bus2sub.csv')
dfb2s = dfb2s[dfb2s['bus_id'].isin(bus_id)]
sub_id = dfb2s['sub_id'].unique()

dfs = pd.read_csv('sub.csv')
dfs = dfs[dfs['sub_id'].isin(sub_id)]
dfs = dfs.reset_index()
dfs.to_csv('Existing_HV_nodes.csv')
sub_loc = dfs[['lat', 'lon']].to_numpy()
del dfb2s, bus_id, dfb, sub_id, Zones, Volt_lim
############################
test_name = "onshoresolar"

mdl = str(sys.argv[1])
wake = int(sys.argv[2])
landr = int(sys.argv[3])
onwindsize = float(sys.argv[4])
solarsize = float(sys.argv[5])
cap_ng = float(sys.argv[6])
cap_cc = float(sys.argv[7])
num_y = int(sys.argv[8])
ensid=int(sys.argv[9])
case_name = sys.argv[10]

datadir = f'/pool001/lyqiu/Siting_Optimization/SensitivityTest_siting_cost_ATB_new/Result_{case_name}/'

prefix='%s/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s' % (datadir,test_name,num_y, ensid, cap_ng*100, cap_cc*100,wake,landr,onwindsize,solarsize,mdl)
cost_df = pd.read_csv(f'{datadir}/onshoresolar_{mdl}_General_Results.csv')

for tech in ['solar-UPV', 'wind-onshore']:
    df = pd.read_csv('%s_%s_locations.csv' % (prefix,tech))
    min_dist_to_HV_node = np.zeros(len(df))
    cost_to_HV_node = np.zeros(len(df))
    exis = np.zeros((len(df), 4))
    for i in range(len(df)):
        loc = np.array(df[['lat', 'lon']].iloc[i])
        # x60 to get distance in miles
        dists = np.linalg.norm(sub_loc-loc, axis=1)*60
        min_dist_to_HV_node[i] = np.min(dists)
        exis[i, 0] = np.int16(np.argmin(dists))
        exis[i, 1] = min_dist_to_HV_node[i]
        exis[i, 2] = dfs['lat'].iloc[np.int16(exis[i, 0])]
        exis[i, 3] = dfs['lon'].iloc[np.int16(exis[i, 0])]
    cost_to_HV_node[i] = max_CF_solar*min_dist_to_HV_node[i] * df['capacity'].iloc[i]*trans_line_cost
    df[['closest_existing_node', 'distance_mile','lat_exist_node', 'lon_exist_node']] = exis
    df.to_csv('%s_%s_locations.csv' % (prefix, tech))
    # print(f'Total transmission line mileage: {np.sum(min_dist_to_HV_node)}')
    # print(f'Total transmission expansion cost for maxSolar: {np.sum(cost_to_HV_node)}')
    idx=get_df_i(cost_df, wake, landr, cap_cc, solarsize, onwindsize, num_y, ensid)
    # add columns to the cost_df if not exist
    if f'{tech}_trans_mile' not in cost_df.columns:
        cost_df[f'{tech}_trans_mile'] = np.nan
    if f'{tech}_trans_cost' not in cost_df.columns:
        cost_df[f'{tech}_trans_cost'] = np.nan
    # add the results to the cost_df
    cost_df.loc[idx,f'{tech}_trans_mile'] = np.sum(min_dist_to_HV_node)
    cost_df.loc[idx,f'{tech}_trans_cost'] = np.sum(cost_to_HV_node)
    cost_df.to_csv(f'{datadir}/onshoresolar_{mdl}_General_Results.csv', index=False)
