# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 11:56:36 2023
Read problem data for the wind-solar siting optimization problem
@author: Rahman Khorramfar
"""
import numpy as np;
import pandas as pd;
import xarray as xr


def get_df(df, wake=None, land=None, cg=None, solarz=None, windz=None, ny=None, ensid=None):
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
    def populate_storage_data(self, Setting):
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
            strg.decay_eff = (1-1/df['duration (hr)'][idx])
            self.Storages.append(strg)
        self.num_storages = len(self.Storages)

class Plant:
    def __init__(self):  # no constructor
        self.Type = str()  # name of the plant type, e.g., solar, wind-offshore
        self.capex = float()
        self.FOM = float()
        # FCR=float();
        self.VOM = float()
        self.heat_rate = float()
        self.lifetime = int()
        self.est_coef = float()

    def populate_plant_data(self, Setting):
        self.Plants = list()
        df = pd.read_csv(f'Plant_params.csv')
        plant_types = Setting.plant_types
        
        for p in range(len(plant_types)):
            plt = Plant()
            plt.Type = plant_types[p]
            idx = np.min(np.where(df['plant_type'] == plt.Type))
            # plt.nameplate_cap = df['Nameplate capacity (MW)'][idx];
            plt.capex = df['CAPEX($/kw)'][idx]*1000  # to MW
            plt.FOM = df['FOM ($/kW-yr)'][idx]*1000  # to MW
            plt.VOM = df['VOM ($/MWh)'][idx]
            plt.heat_rate = df['Heat Rate  (MMBtu/MWh)'][idx]
            plt.lifetime = int(df['Lifetime (year)'][idx])
            plt.est_coef = Setting.WACC * \
                ((1+Setting.WACC)**plt.lifetime) / \
                ((1+Setting.WACC)**plt.lifetime-1)
            self.Plants.append(plt)
        self.num_plants = len(self.Plants)

class REDat:
    def __init__(self):  # no constructor
        self.Type = str()
        self.CF = list()
        self.lat = list()
        self.lon = list()
        self.area = list()
        self.num_loc = int()
    def ReadREData(self,Setting,loaddata):
        self.REPlants = list();
        plant_types = Setting.RE_plant_types;
        load_data=pd.read_csv(loaddata)
        for p in range(len(plant_types)):
            red = REDat();
            red.Type = plant_types[p];
            red.power = load_data[f'{red.Type}_generation']
            red.capacity = pd.read_csv('./Results/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_%s_locations.csv' % (
                Setting.test_name, Setting.num_y, Setting.ens_id, Setting.UB_dispatchable_cap['ng']*100, Setting.UB_dispatchable_cap['CCGT']*100, 
                Setting.wake, Setting.landr, Setting.RE_cell_size['wind-onshore'], Setting.RE_cell_size['solar-UPV'], 
                Setting.weather_model, red.Type))['capacity'].to_numpy().sum()
            self.REPlants.append(red);
        self.num_re_plants=len(self.REPlants);

class Data(REDat,Plant,Storage):
    def __init__(self,Setting):  # no constructor
        super().__init__()
        loaddata='./Results/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_Load.csv'%(Setting.test_name,Setting.num_y, Setting.ens_id, 
                                                                                                                        Setting.UB_dispatchable_cap['ng']*100,
                                                                                                                         Setting.UB_dispatchable_cap['CCGT']*100, 
        Setting.wake, Setting.landr, Setting.RE_cell_size['wind-onshore'], Setting.RE_cell_size['solar-UPV'], Setting.weather_model)
        self.ReadREData(Setting,loaddata);
        self.populate_plant_data(Setting);
        self.populate_storage_data(Setting);
        load_data=pd.read_csv(loaddata)
        self.demand = load_data['demand'].to_numpy();
        #self.curtail=load_data['Curtail'].to_numpy();
        #self.LL=load_data['LL'].to_numpy();
        self.num_plan_periods = len(self.demand);


