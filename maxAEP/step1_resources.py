# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 15:18:12 2023

@author: Rahman Khorramfar
"""

import numpy as np
import pandas as pd
import xarray as xr
import sys
import itertools


def get_df(df, wake=None, land=None, cg=None, solarz=None, windz=None, ny=None,ensid=None):
    df = df.reset_index()
    df = df.set_index(['wake_allowd', 'landres_allowed', 'upper_bound_CCGT',
                      'cell_size_solar-UPV', 'cell_size_wind-onshore', 'num_yr','ens_id'])
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
    return dfa

class Setting:
    demandfile = str()
    REfile = dict()
    RE_capacity_density = dict()  # MW/km2
    RE_cell_size = dict()  # degree
    RE_plant_types = list()  # set of RE plant types considered
    solver_gap = float()
    wall_clock_time_lim = int()
    weather_model = str()
    print_results_header = bool()
    print_detailed_results = bool()
    test_name = str()
    consider_land_area = bool()
    consider_wind_wake = bool()
    datadir = str()
    REfilemean = dict()
    wake = int()
    landr = int()
    num_y = int()
    sub_year_list = list()
    ens_id = int()
    year_list = list()

Setting.demandfile = '../Demand/ISONE_grossload_metdata_spliced_22yr_UTC0.csv'
Setting.RE_plant_types = ['solar-UPV', 'wind-onshore']
Setting.print_results_header = 1
Setting.print_detailed_results = 1
Setting.test_name = 'onshoresolar'
Setting.RE_capacity_density['wind-onshore'] = 3.1158
Setting.RE_capacity_density['solar-UPV'] = 24
csvdir = '../Result_minCost/'
datadir = '../CF_Data/'
Setting.year_list = [2007, 2008, 2009, 2010, 2011, 2012, 2013]

def runmodel(datadir, csvdir, Setting, mdl, wake, landr, onwindsize, solarsize, ng_thres, cc_thres, sub_year_list, ens_id):
    Setting.num_y = len(sub_year_list)
    Setting.sub_year_list = sub_year_list
    Setting.ens_id = ens_id

    if wake == 1:
        if mdl == "WRHigh":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/wakecf/WTK_wakecf64_IEA_3.4MW_130_onshore_%.2fdeg_' % (datadir, mdl, onwindsize)
        elif mdl == "WRLow":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/wakecf/ERA5_wakecf16_IEA_3.4MW_130_onshore_%.2fdeg_' % (datadir, mdl, onwindsize)
    else:
        if mdl == "WRHigh":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/simplecf/WTK_simplecf_IEA_3.4MW_130_onshore_%.2fdeg_' % (datadir, mdl, onwindsize)
        elif mdl == "WRLow":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/simplecf/ERA5_simplecf_IEA_3.4MW_130_onshore_%.2fdeg_' % (datadir, mdl, onwindsize)

    Setting.RE_cell_size['wind-onshore'] = onwindsize
    Setting.RE_cell_size['solar-UPV'] = solarsize

    if mdl == "WRHigh":
        Setting.REfile['solar-UPV'] = '%s/%s/Solar/NSRDB_SAM_UTC_%.2f_cf_' % (datadir, mdl,solarsize)
    else:
        Setting.REfile['solar-UPV'] = '%s/%s/Solar/ERA5_SAM_UTC_%.2f_cf_' % (datadir, mdl, solarsize)

    # Tesing setting
    cp_data = pd.read_csv(f'{csvdir}{Setting.test_name}_{mdl}_General_Results.csv')
    # print()
    cp0 = get_df(cp_data, wake=wake, land=landr, cg=cc_thres,ensid=ens_id,ny=Setting.num_y,solarz=Setting.RE_cell_size['solar-UPV'], windz=Setting.RE_cell_size['wind-onshore'])
    

    DF_Load = pd.DataFrame()
    for retype in Setting.RE_plant_types:
        data = pd.read_csv(Setting.REfile[retype]+'2007_2013_timmean_ranked.csv')
        AEP = cp0[f'prod_{retype}'].values
        #print(cp0[f'capacity_{retype}'].values)
        cumulative_AEP = 0
        if landr == 0:
            data['AEP'] = data['area'] * Setting.RE_capacity_density[retype]*data['cf']*8760
            data['capacity'] = data['area']*Setting.RE_capacity_density[retype]
        else:
            data['AEP'] = data['restricted_area'] * Setting.RE_capacity_density[retype]*data['cf']*8760
            data['capacity'] = data['restricted_area'] * Setting.RE_capacity_density[retype]
        data = data.sort_values(by='AEP', ascending=False)

        for i in range(len(data)):
            cumulative_AEP = cumulative_AEP + data.iloc[i]['AEP']
            if cumulative_AEP >= AEP:
                break

        AEP_selected = data[0:i+1].copy()
        corrected_capacity = AEP_selected.iloc[i]['capacity']*(AEP-cumulative_AEP+AEP_selected.iloc[i]['AEP'])/AEP_selected.iloc[i]['AEP']
        AEP_selected.at[AEP_selected.index[i],'capacity']=corrected_capacity[0]
        DF_locations = AEP_selected[['lat', 'lon', 'capacity']].copy()
        DF_locations.to_csv('./Results/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_%s_locations.csv' % (
            Setting.test_name, num_y,ens_id, int(ng_thres*100), int(cc_thres*100), wake, landr, onwindsize, solarsize, mdl, retype))
        power = []
        for iy in Setting.sub_year_list:
            CF_orig = xr.open_dataset(Setting.REfile[retype]+str(iy)+'.nc')['cf']
            CF_orig['lat'] = CF_orig['lat'].round(2)
            CF_orig['lon'] = CF_orig['lon'].round(2)
            CF_orig = CF_orig.stack(z=("lat", "lon")).dropna('z', how='all')
            CF_orig = CF_orig.sel(
            time=~((CF_orig.time.dt.month == 2) & (CF_orig.time.dt.day == 29)))
            CF_orig_selected = CF_orig.sel(
                z=DF_locations.set_index(['lat', 'lon']).index.values)
            power_yr = (CF_orig_selected *
                        DF_locations['capacity'].values).sum(dim='z').values
            power.append(power_yr)
        power = np.concatenate(power, axis=0)
        DF_Load[retype+'_generation'] = power

    orig_load = pd.read_csv('%s%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_Load.csv' %
                            (csvdir, Setting.test_name, num_y, ens_id, int(ng_thres*100), int(cc_thres*100), wake, landr, onwindsize, solarsize, mdl))

    DF_Load['demand'] = orig_load['demand'].values
    DF_Load.to_csv('./Results/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_Load.csv' %
                   (Setting.test_name, num_y, ens_id, int(ng_thres*100), int(cc_thres*100), wake, landr, onwindsize, solarsize, mdl))


mdl = str(sys.argv[1])
wake = int(sys.argv[2])
landr = int(sys.argv[3])
onwindsize = float(sys.argv[4])
solarsize = float(sys.argv[5])
cap_ng = float(sys.argv[6])
cap_cc = float(sys.argv[7])
num_y = int(sys.argv[8])
ensid = int(sys.argv[9])

year_lists = list(itertools.combinations(Setting.year_list, num_y))
print(year_lists[ensid-1])

print(mdl)
runmodel(datadir, csvdir, Setting, mdl, wake, landr, onwindsize,
         solarsize, cap_ng, cap_cc, year_lists[ensid-1], ensid)
