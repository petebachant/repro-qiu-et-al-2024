# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 15:18:12 2023

"""
import numpy as np
import pandas as pd
import NCDataCost
import Modules_cost as Modules
import gurobipy as gp
from gurobipy import GRB
import time
import sys
import itertools

class Setting:
    RE_capacity_density = dict()  # MW/km2
    RE_cell_size = dict()  # degree
    RE_plant_types = list()  # set of RE plant types considered
    solver_gap = float()
    wall_clock_time_lim = int()
    weather_model = str()
    print_results_header = bool()
    print_detailed_results = bool()
    test_name = str()
    datadir = str()
    UB_dispatchable_cap = dict()
    lost_load_thres = float()
    gas_price = float()
    storage_types = list()
    plant_types = list()
    wake = int()
    gas_plant_types = list()
    val_lost_load = float()
    val_curtail = float()
    num_y = int()
    sub_year_list = list()
    ens_id = int()

# Setting parameters
Setting.solver_gap = 0.001  # x100 percent
Setting.wall_clock_time_lim = 10000  # seconds
Setting.RE_plant_types = ['solar-UPV', 'wind-onshore']
Setting.gas_plant_types = ['ng', 'CCGT']
Setting.plant_types = Setting.RE_plant_types + Setting.gas_plant_types
Setting.print_results_header = 1
Setting.print_detailed_results = 1
Setting.RE_lev = 0.5
Setting.WACC = 0.071
Setting.lost_load_thres = 0.0
Setting.val_lost_load = 10000
Setting.gas_price = 5.45
Setting.storage_types = ['Li-ion']
Setting.test_name = "onshoresolar"
Setting.datadir = f'./Results/{Setting.test_name}'
Setting.year_list = [2007, 2008, 2009, 2010, 2011, 2012, 2013]

def runmodel(Setting, mdl, wake, landr, onwindsize, solarsize, cap_ng, cap_cc,sub_year_list, ens_id):
    Setting.num_y = len(sub_year_list)
    Setting.sub_year_list = sub_year_list
    Setting.ens_id = ens_id
    # GW to MW # currently the ISO-NE cap is 31 GW
    Setting.UB_dispatchable_cap['ng'] = cap_ng
    Setting.UB_dispatchable_cap['CCGT'] = cap_cc  # GW to MW
    Setting.weather_model = mdl
    Setting.wake = wake
    Setting.landr = landr
    Setting.RE_cell_size['wind-onshore'] = onwindsize
    Setting.RE_cell_size['solar-UPV'] = solarsize
    stime = time.time()
    dat = NCDataCost.Data(Setting)
    Model = gp.Model()
    Modules.define_DVs(dat, Setting, Model)
    Modules.add_constraints(dat, Setting, Model)
    obj = Modules.add_obj_func(dat, Setting, Model)
    Model.modelSense = GRB.MINIMIZE
    Model.setObjective(obj)
    Model.setParam('OutputFlag', 1)
    Model.setParam('MIPGap', Setting.solver_gap)
    Model.setParam('Timelimit', Setting.wall_clock_time_lim)
    Model.setParam('Presolve', 2)  # -1 to 2
    Model.optimize()
    Modules.get_DV_vals(Model)
    Modules.print_results(dat, Setting, stime, Model)

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
runmodel(Setting, mdl, wake, landr, onwindsize, solarsize,
         cap_ng, cap_cc, year_lists[ensid-1], ensid)
