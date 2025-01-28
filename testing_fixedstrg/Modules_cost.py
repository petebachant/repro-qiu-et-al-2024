# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 08:36:23 2023
Last Update: 2023 Oct 17
@original author: Rahman Khorramfar
@modified by: Liying Qiu
"""

import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB, quicksum, LinExpr
from DVs_cost import DV
import time,os,csv


def fetch_data(dat, Setting):
    global nT, nPlt, nREPlt, nDPlt, nStr, nYear, RE_cost, gas_inv_cost, strg_inv_cost,Xr,Xstr,Xg
    nT = dat.demand.shape[0]
    nPlt = dat.num_plants  # number of power plants types
    nREPlt = dat.num_re_plants  # number of RE plants types
    nStr = dat.num_storages  # =1, only one storage is considered
    nYear = Setting.num_y
    nDPlt = len(Setting.gas_plant_types)
    Xr=[]
    RE_cost = []
    gas_inv_cost = list()
    for dpland in Setting.gas_plant_types:
        pindex = Setting.plant_types.index(dpland)
        dd = dat.Plants[pindex]
        single_cost = nYear*(dd.est_coef*dd.capex+dd.FOM)
        gg_cost=single_cost* dat.Plants[pindex].capacity
        gas_inv_cost.append(gg_cost)
        Xg = dat.Plants[pindex].capacity

    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        pindex = Setting.plant_types.index(repland)
        dd = dat.Plants[pindex]
        single_cost = (dd.est_coef * dd.capex+dd.FOM)
        Xr.append(dat.REPlants[rindex].capacity)
        RE_cost.append(single_cost*dat.REPlants[rindex].capacity)
    
    dd = dat.Storages[0]
    strg_inv_cost = (dd.est_coef*dd.capex+dd.FOM)*dat.Storages[0].sLev
    Xstr=dat.Storages[0].sLev
    



# define decision variables
def define_DVs(dat, Setting, Model):
    fetch_data(dat, Setting)
    # Other Decisions
    DV.prod = Model.addVars(nPlt, nT, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
    DV.Curtail = Model.addVars(nT, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
    DV.LL = Model.addVars(nT, lb=0, ub=GRB.INFINITY,vtype=GRB.CONTINUOUS)  # lost load
    DV.sCh = Model.addVars(nT, lb=0, ub=GRB.INFINITY,vtype=GRB.CONTINUOUS)  # storage charged, MW
    DV.sDis = Model.addVars(nT, lb=0, ub=GRB.INFINITY,vtype=GRB.CONTINUOUS)  # storage discharged, MW
    DV.sLev=Model.addVars(nT,lb=0,ub=GRB.INFINITY,vtype=GRB.CONTINUOUS) # storage level, MWh

def add_obj_func(dat, Setting, Model):
    DV.total_cost = Model.addVar(vtype=GRB.CONTINUOUS)
    DV.fuel_cost = Model.addVars(nDPlt, vtype=GRB.CONTINUOUS)
    DV.var_cost = Model.addVars(nDPlt, vtype=GRB.CONTINUOUS)
    DV.lost_load_cost = Model.addVar(vtype=GRB.CONTINUOUS)
    # DV.curtail_cost=Model.addVar(vtype = GRB.CONTINUOUS);

    obj = gp.LinExpr()


    var_cost = list()
    fuel_cost = list()
    for dpland in Setting.gas_plant_types:
        pindex = Setting.plant_types.index(dpland)
        dd = dat.Plants[pindex]

        vv_cost = gp.LinExpr()
        ff_cost = gp.LinExpr()
        for t in range(nT):
            vv_cost.addTerms(dd.VOM, DV.prod[pindex, t])
            ff_cost.addTerms(Setting.gas_price*dd.heat_rate,DV.prod[pindex, t])
        obj += vv_cost
        obj += ff_cost
        var_cost.append(vv_cost)
        fuel_cost.append(ff_cost)


    lost_load_cost=gp.LinExpr();
    for t in range(nT):
        lost_load_cost.addTerms(Setting.val_lost_load,DV.LL[t]);
    obj+=lost_load_cost;

    Model.addConstr(DV.total_cost == obj)
    for d in range(nDPlt):
        Model.addConstr(DV.var_cost[d] == var_cost[d])
        Model.addConstr(DV.fuel_cost[d] == fuel_cost[d])
    Model.addConstr(DV.lost_load_cost == lost_load_cost)
    return obj


def add_constraints(dat, Setting, Model):
    # c1: production < capacity
    for dpland in Setting.gas_plant_types:
        dindex = Setting.gas_plant_types.index(dpland)
        pindex = Setting.plant_types.index(dpland)
        Model.addConstrs(DV.prod[pindex, t] <= Xg for t in range(nT))
    
    # c3: upper bound for renewable energy generation capacity
    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        pindex = Setting.plant_types.index(repland)
        for t in range(nT):
            Model.addConstr(DV.prod[pindex, t] == dat.REPlants[rindex].prod[t],name=f'c_REprod_{t}_{repland}')

    # c4: balance constraints
    for t in range(nT):
        lhs_expr = gp.LinExpr()
        for p in range(nPlt):
            lhs_expr.addTerms(1, DV.prod[p, t])
        lhs_expr.addTerms(1, DV.sDis[t])
        lhs_expr.addTerms(1, DV.LL[t])
        lhs_expr.addTerms(-1, DV.sCh[t])
        lhs_expr.addTerms(-1, DV.Curtail[t])
        Model.addConstr(lhs_expr == dat.demand[t], name=f'c_demand_{t}')

    # c5: storage constraints
    dd = dat.Storages[0]
    Model.addConstrs(DV.sCh[t] <= (Xstr/dd.duration) for t in range(nT))
    Model.addConstrs(DV.sDis[t] <= (Xstr/dd.duration) for t in range(nT))
    Model.addConstrs(DV.sLev[t] <= Xstr for t in range(0, nT))
    Model.addConstrs(DV.sDis[t] <= DV.sLev[t-1] for t in range(1, nT))
    Model.addConstrs(DV.sLev[t] == DV.sLev[t-1] + dd.eff_round *
                     DV.sCh[t]-DV.sDis[t] for t in range(1, nT))


    # c8: curt smaller than generations
    for t in range(nT):
        prodt = gp.LinExpr()
        for pindex in range(nPlt):
            prodt.addTerms(1, DV.prod[pindex, t])
        Model.addConstr(DV.Curtail[t] <= prodt, name=f'curl')
    

def get_DV_vals(Model, Setting):
    DV.var_cost_val = Model.getAttr('x', DV.var_cost)
    DV.fuel_cost_val = Model.getAttr('x', DV.fuel_cost)
    DV.prod_val = Model.getAttr('x', DV.prod)
    DV.sDis_val = Model.getAttr('x', DV.sDis)
    DV.sLev_val = Model.getAttr('x', DV.sLev)
    DV.sCh_val = Model.getAttr('x', DV.sCh)
    DV.LL_val = Model.getAttr('x',DV.LL);
    DV.Curtail_val = Model.getAttr('x', DV.Curtail)
    # DV.Curtail_val = Model.getAttr('x', DV.Curtail)
    # get costs
    DV.total_cost_val = DV.total_cost.X+sum(RE_cost)+sum(gas_inv_cost)+strg_inv_cost
    DV.lost_load_cost_val = DV.lost_load_cost.X;
    # DV.curtail_cost_val = DV.curtail_cost.X

def print_results(dat, Setting, stime, Model):
    current_path = os.getcwd()

    prod_value = np.zeros((nPlt, nT))
    for p in range(nPlt):
        for t in range(nT):
            prod_value[p, t] = DV.prod_val[p, t]
    if Setting.print_detailed_results == 1:
        DF_prod = pd.DataFrame()
        for plant in Setting.plant_types:
            pindex = Setting.plant_types.index(plant)
            DF_prod[f'prod_{plant}'] = prod_value[pindex, :].squeeze()
        DF_prod['sLev'] = DV.sLev_val
        DF_prod['sCh'] = DV.sCh_val
        DF_prod['sDis'] = DV.sDis_val
        DF_prod['demand'] = dat.demand
        DF_prod['LL'] = DV.LL_val
        DF_prod['Curt'] = DV.Curtail_val
        DF_prod['Date'] = dat.dates
        csvfilename_suffix = '%s/Result_%s/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s' % (current_path, Setting.case, Setting.test_name, Setting.eva_num_y, Setting.ens_id,
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
        DF_prod.to_csv(csvfilename_suffix+'_Load.csv',
                       encoding='utf-8', index=False)
    total_load = dat.demand.sum()
    
    DF = pd.DataFrame(data={'num_periods': nT,
                            'num_vars': Model.NumVars,
                            'num_constrs': Model.NumConstrs,
                            'Sol_time': np.round(time.time()-stime),
                            'total_cost': DV.total_cost_val,
                            'total_cost_strg': strg_inv_cost,
                            'prod_strg': (DV.sDis_val.sum())/nYear,
                            'capacity_strg': dat.Storages[0].sLev,
                            'LL_cost': DV.lost_load_cost_val/nYear,
                            'curtail_cost': 0,
                            'total_LL': DV.LL_val.sum(),
                            'total_Curtail': DV.Curtail_val.sum()/nYear,
                            'eval_years': str(Setting.eva_years),
                            'test_years': str(Setting.test_year),
                            'num_y': Setting.eva_num_y,
                            'ens_id': Setting.ens_id,
                            'weather_model': Setting.weather_model,
                            'wake_allowd': Setting.wake,
                            'landres_allowed': Setting.landr,
                            'total_load': total_load,
                            'LCOE': DV.total_cost_val/(total_load*1000)}, index=[0])
    for dpland in Setting.gas_plant_types:
        dindex = Setting.gas_plant_types.index(dpland)
        pindex = Setting.plant_types.index(dpland)
        DF[f'inv_cost_{dpland}'] =  gas_inv_cost[dindex]
        DF[f'fuel_cost_{dpland}'] = DV.fuel_cost_val[dindex]
        DF[f'var_cost_{dpland}'] = DV.var_cost_val[dindex]
        DF[f'prod_{dpland}'] = prod_value[pindex, :].sum()/nYear
        DF[f'capacity_{dpland}'] = dat.Plants[pindex].capacity
        DF[f'total_cost_{dpland}'] = gas_inv_cost[dindex] + DV.fuel_cost_val[dindex]+DV.var_cost_val[dindex]
        DF[f'upper_bound_{dpland}'] = Setting.UB_dispatchable_cap[dpland]


    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        pindex = Setting.plant_types.index(repland)
        DF[f'inv_cost_{repland}'] = RE_cost[rindex]
        DF[f'prod_{repland}'] = prod_value[pindex, :].sum()/nYear
        print(dat.Plants[pindex].capacity)
        DF[f'capacity_{repland}'] = dat.Plants[pindex].capacity
        DF[f'cell_size_{repland}'] = Setting.RE_cell_size[repland]
        DF[f'total_cost_{repland}'] = RE_cost[rindex]
    dfvfile = f'{current_path}/Result_{Setting.case}/{Setting.test_name}_{Setting.weather_model}_General_Results.csv'
    if os.path.exists(dfvfile):
        DF.to_csv(dfvfile, mode='a', header=False, index=False)
    else:
        DF.to_csv(dfvfile, mode='w', header=True, index=False)



