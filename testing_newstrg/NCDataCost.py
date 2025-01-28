# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 11:56:36 2023
Read problem data for the wind-solar siting optimization problem
@author: Rahman Khorramfar
"""
import numpy as np;
import pandas as pd;
import xarray as xr
# import math


def get_df(df, wake=None, land=None, cg=None, solarz=None, windz=None, ny=None, ensid=None):
    df = df.reset_index(drop=True)
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
    return dfa

class Storage:
    def __init__(self):  # no constructor
        self.Type = str()
        self.capex = float()
        self.eff_round = float()
        self.FOM = float()
        self.lifetime = int()
        self.est_coef = float()
        self.num_storages = []
        self.duration = int()
        self.decay_eff = float()
        # self.sLev=float()
        # self.invcost=float()
    def populate_storage_data(self, cp_dta,Setting):
        self.Storages = list()
        df = pd.read_csv(f'Storage_params.csv')
        storage_types = Setting.storage_types
        for s in range(len(storage_types)):
            strg = Storage()
            strg.Type = storage_types[s]
            idx = np.min(np.where(df['Storage technology'] == strg.Type))
            strg.capex = (df['energy capex($/kWh)'][idx]+df['power capex($/kW)']
                          [idx]/df['duration (hr)'][idx])*1000  # per MWh
            strg.eff_round = df['round-trip efficiency'][idx]
            strg.FOM = strg.capex*0.025
            strg.lifetime = int(df['lifetime'][idx])  # yr
            strg.est_coef = Setting.WACC * \
                ((1+Setting.WACC)**strg.lifetime) / \
                ((1+Setting.WACC)**strg.lifetime-1)
            strg.duration = int(df['duration (hr)'][idx])  # hr
            # strg.sLev=cp_dta[f'capacity_strg'].values[0]
            # strg.invcost = cp_dta[f'total_cost_strg'].values[0]
            self.Storages.append(strg)
        self.num_storages = len(self.Storages)

class Plant:
    def __init__(self):  # no constructor
        self.Type = str()   
        self.capex = float()
        self.FOM = float()
        self.VOM = float()
        self.heat_rate = float()
        self.lifetime = int()
        self.est_coef = float()

        self.capacity=float()
        self.invcost = float()

    def populate_plant_data(self,cp_data,Setting):
        self.Plants = list()
        df = pd.read_csv(f'Plant_params.csv')
        plant_types = Setting.plant_types
        for p in range(len(plant_types)):
            plt = Plant()
            plt.Type = plant_types[p]
            idx = np.min(np.where(df['plant_type'] == plt.Type))
            plt.capex = df['CAPEX($/kw)'][idx]*1000  # to MW
            plt.FOM = df['FOM ($/kW-yr)'][idx]*1000  # to MW
            plt.VOM = df['VOM ($/MWh)'][idx]
            plt.heat_rate = df['Heat Rate  (MMBtu/MWh)'][idx]
            plt.lifetime = int(df['Lifetime (year)'][idx])
            plt.est_coef = Setting.WACC * \
                ((1+Setting.WACC)**plt.lifetime) / \
                ((1+Setting.WACC)**plt.lifetime-1)
            plt.capacity=cp_data[f'capacity_{plt.Type}'].values[0]
            plt.invcost = cp_data[f'inv_cost_{plt.Type}'].values[0]
            self.Plants.append(plt)
        self.num_plants = len(self.Plants)

class REDat:
    def __init__(self):  # no constructor
        self.Type = str()
        self.capacity=float();
        self.prod=list()
        self.invcost=float();

    def ReadREData(self, cp_data,Setting):
        self.REPlants = list()
        plant_types = Setting.RE_plant_types
        for p in range(len(plant_types)):
            red = REDat()
            red.Type = plant_types[p]
            csvfilename_suffix = '%s/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s' % (Setting.csvdir, Setting.test_name, Setting.eva_num_y, Setting.ens_id,
                                                                                                                                  Setting.UB_dispatchable_cap[
                                                                                                                                      'ng']*100,
                                                                                                                                  Setting.UB_dispatchable_cap[
                                                                                                                                      'CCGT']*100,
                                                                                                                                  Setting.wake, Setting.landr,
                                                                                                                                  Setting.RE_cell_size[
                                                                                                                                      'wind-onshore'],
                                                                                                                                  Setting.RE_cell_size[
                                                                                                                                      'solar-UPV'],
                                                                                                                                  Setting.weather_model)

            locations = pd.read_csv(
                csvfilename_suffix+f'_{red.Type}_locations.csv')
            locations['lat'] = locations['lat'].round(2)
            locations['lon'] = locations['lon'].round(2)
            power = []
            for iy in Setting.test_year:
                CF_orig = xr.open_dataset(
                    Setting.REfile[red.Type]+str(iy)+'.nc')['cf']
                CF_orig['lat'] = CF_orig['lat'].round(2)
                CF_orig['lon'] = CF_orig['lon'].round(2)
                CF_orig = CF_orig.stack(z=("lat", "lon")).dropna('z', how='all')
                CF_orig = CF_orig.sel(
                time=~((CF_orig.time.dt.month == 2) & (CF_orig.time.dt.day == 29)))
                CF_orig_selected = CF_orig.sel(
                    z=locations.set_index(['lat', 'lon']).index.values)
                power_yr=(CF_orig_selected *locations['capacity'].values).sum(dim='z').values
                power.append(power_yr)
                
            power=np.concatenate(power,axis=0)
            #to pd dataframe
            red.prod=power
            red.capacity=cp_data[f'capacity_{red.Type}'].values
            red.invcost = cp_data[f'inv_cost_{red.Type}'].values
            self.REPlants.append(red)
        self.num_re_plants = len(self.REPlants)

class Data(REDat,Plant,Storage):
    def __init__(self, Setting):  # no constructor
        super().__init__()
        cp_data = pd.read_csv(f'{Setting.csvdir}{Setting.test_name}_{Setting.weather_model}_General_Results.csv')
        cp_data = get_df(cp_data,wake= Setting.wake,
                         land= Setting.landr,
                         cg=Setting.UB_dispatchable_cap['CCGT'],
                         solarz=Setting.RE_cell_size['solar-UPV'],
                         windz=Setting.RE_cell_size['wind-onshore'],
                         ny=Setting.eva_num_y,
                         ensid=Setting.ens_id)

        self.ReadREData(cp_data, Setting)
        self.populate_plant_data(cp_data, Setting)
        self.populate_storage_data(cp_data, Setting)

        df = pd.read_csv(Setting.demandfile)
        dft = df.set_index(pd.to_datetime(df['Date'], format='%m/%d/%y'))
        dft = dft.loc[dft.index.year.isin(Setting.test_year)]
        dft = dft.loc[~((dft.index.month == 2) & (dft.index.day == 29))]
        self.demand = dft['ISONE_grs_ld'].to_numpy()
        self.dates=dft.index
        self.num_plan_periods = len(self.demand)


