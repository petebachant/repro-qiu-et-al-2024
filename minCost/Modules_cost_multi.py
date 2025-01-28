# -*- coding: utf-8 -*-
"""
Last Update: 2024-02-09
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
    global nT, nPlt, nREPlt, nDPlt, nStr, nYear, RE_nlocations
    RE_nlocations = list()
    for replant in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(replant)
        RE_nlocations.append(dat.REPlants[rindex].num_loc)
    nT = dat.demand.shape[0]
    nPlt = dat.num_plants  # number of power plants types
    nREPlt = dat.num_re_plants  # number of RE plants types
    nStr = dat.num_storages  # =1, only one storage is considered
    nYear = Setting.num_y
    nDPlt = len(Setting.gas_plant_types)

# define decision variables
def define_DVs(dat, Setting, Model):
    fetch_data(dat, Setting)
    DV.Xr = list()  # capacity of of RE farm
    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        DV.Xr.append(Model.addVars(
            RE_nlocations[rindex], lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS))
    DV.Xstr = Model.addVar(lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
    DV.Xg = Model.addVars(nDPlt, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
    # Other Decisions
    DV.prod = Model.addVars(nPlt, nT, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
    DV.load = Model.addVars(nPlt, nT, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
    DV.LL = Model.addVars(nT, lb=0, ub=GRB.INFINITY,vtype=GRB.CONTINUOUS)  # lost load
    DV.sCh = Model.addVars(nT, lb=0, ub=GRB.INFINITY,vtype=GRB.CONTINUOUS)  # storage charged, MW
    DV.sDis = Model.addVars(nT, lb=0, ub=GRB.INFINITY,vtype=GRB.CONTINUOUS)  # storage discharged, MW
    # accumulated storage level, MWh
    DV.sLev = Model.addVars(nT, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)

def add_obj_func(dat, Setting, Model):
    DV.total_cost = Model.addVar(vtype=GRB.CONTINUOUS)
    DV.RE_cost = Model.addVars(nREPlt, vtype=GRB.CONTINUOUS)
    DV.fuel_cost = Model.addVars(nDPlt, vtype=GRB.CONTINUOUS)
    DV.gas_inv_cost = Model.addVars(nDPlt, vtype=GRB.CONTINUOUS)
    DV.var_cost = Model.addVars(nDPlt, vtype=GRB.CONTINUOUS)
    DV.strg_inv_cost = Model.addVar(vtype=GRB.CONTINUOUS)
    #DV.lost_load_cost = Model.addVar(vtype=GRB.CONTINUOUS)
    # DV.curtail_cost=Model.addVar(vtype = GRB.CONTINUOUS);

    obj = gp.LinExpr()
    RE_cost = list()
    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        pindex = Setting.plant_types.index(repland)
        dd = dat.Plants[pindex]
        single_cost = (dd.est_coef * dd.capex+dd.FOM)
        r_cost = gp.LinExpr()
        for i in range(RE_nlocations[rindex]):
            r_cost.addTerms(single_cost, DV.Xr[rindex][i])
        obj += r_cost
        RE_cost.append(r_cost)
        
    gas_inv_cost = list()
    var_cost = list()
    fuel_cost = list()
    for dpland in Setting.gas_plant_types:
        pindex = Setting.plant_types.index(dpland)
        dindex = Setting.gas_plant_types.index(dpland)
        gg_cost = gp.LinExpr()
        dd = dat.Plants[pindex]
        single_cost = (dd.est_coef*dd.capex+dd.FOM)
        gg_cost.addTerms(single_cost, DV.Xg[dindex])
        obj += gg_cost
        gas_inv_cost.append(gg_cost)

        vv_cost = gp.LinExpr()
        ff_cost = gp.LinExpr()
        for t in range(nT):
            vv_cost.addTerms(dd.VOM/nYear, DV.prod[pindex, t])
            ff_cost.addTerms(Setting.gas_price*dd.heat_rate/nYear, DV.prod[pindex, t])
        obj += vv_cost
        obj += ff_cost
        var_cost.append(vv_cost)
        fuel_cost.append(ff_cost)

    strg_inv_cost = gp.LinExpr()
    dd = dat.Storages[0]
    strg_inv_cost.addTerms((dd.est_coef*dd.capex+dd.FOM), DV.Xstr)
    obj += strg_inv_cost

    Model.addConstr(DV.total_cost == obj)
    for r in range(nREPlt):
        Model.addConstr(DV.RE_cost[r] == RE_cost[r])
    Model.addConstr(DV.strg_inv_cost == strg_inv_cost)
    for d in range(nDPlt):
        Model.addConstr(DV.gas_inv_cost[d] == gas_inv_cost[d])
        Model.addConstr(DV.var_cost[d] == var_cost[d])
        Model.addConstr(DV.fuel_cost[d] == fuel_cost[d])
    return obj


def add_constraints(dat, Setting, Model):
    # c1: production < capacity            
    for dpland in Setting.gas_plant_types:
        dindex = Setting.gas_plant_types.index(dpland)
        pindex = Setting.plant_types.index(dpland)
        Model.addConstrs(DV.prod[pindex, t] <= DV.Xg[dindex]for t in range(nT))
    # c2: vRES: production = CF*capacity
    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        pindex = Setting.plant_types.index(repland)
        for t in range(nT):
            lhs_expr = gp.LinExpr()
            for i in range(RE_nlocations[rindex]):
                lhs_expr.addTerms(dat.REPlants[rindex].CF[t, i], DV.Xr[rindex][i])
            Model.addConstr(DV.prod[pindex, t] == lhs_expr,name=f'c_REprod_{t}_{repland}')
    # c3: renewalbe target
    for dpland in Setting.gas_plant_types:
        pindex = Setting.plant_types.index(dpland)
        ff_load = gp.LinExpr()
        for t in range(nT):
            ff_load.addTerms(1, DV.load[pindex, t])
        Model.addConstr(ff_load <= dat.demand.sum()*Setting.UB_dispatchable_cap[dpland], name=f'c_ffload_cap_{dpland}')
    # c4: balance constraints
    for t in range(nT):
        lhs_expr = gp.LinExpr()
        for p in range(nPlt):
            lhs_expr.addTerms(1, DV.load[p, t])
        lhs_expr.addTerms(1, DV.sDis[t])
        lhs_expr.addTerms(1, DV.LL[t])
        lhs_expr.addTerms(-1, DV.sCh[t])
        # lhs_expr.addTerms(-1, DV.Curtail[t])  # !!
        Model.addConstr(lhs_expr == dat.demand[t], name=f'c_demand_{t}')

    # c5: storage constraints
    dd = dat.Storages[0]
    Model.addConstrs(DV.sCh[t] <= (DV.Xstr/dd.duration) for t in range(nT))
    Model.addConstrs(DV.sDis[t] <= (DV.Xstr/dd.duration) for t in range(nT))
    Model.addConstrs(DV.sLev[t] <= DV.Xstr for t in range(1, nT))
    Model.addConstrs(DV.sDis[t] <= DV.sLev[t-1] for t in range(1, nT))
    Model.addConstrs(DV.sLev[t] == DV.sLev[t-1] + dd.eff_round *
                     DV.sCh[t]-DV.sDis[t] for t in range(1, nT))
    Model.addConstr(DV.sLev[0] == DV.Xstr)


    # c6: RE farm size
    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        for i in range(RE_nlocations[rindex]):
            Model.addConstr(DV.Xr[rindex][i] <= dat.REPlants[rindex].area[i] *
                            Setting.RE_capacity_density[repland], name=f'c_REsize_{i}_{repland}')
    # c7: allowed lost load
    Model.addConstrs(DV.LL[t] <= Setting.lost_load_thres for t in range(nT))

    # c8: actual load: smaller than generations
    for pindex in range(nPlt):
        for t in range(nT):
            Model.addConstr(DV.load[pindex, t] <= DV.prod[pindex, t], name=f'c_load_{t}_{pindex}')

def get_DV_vals(Model, Setting):
    DV.Xr_val = list()
    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        DV.Xr_val.append(Model.getAttr('x', DV.Xr[rindex]))
    DV.load_val = Model.getAttr('x', DV.load)
    DV.Xg_val = Model.getAttr('x', DV.Xg)
    DV.gas_inv_cost_val = Model.getAttr('x', DV.gas_inv_cost)
    DV.var_cost_val = Model.getAttr('x', DV.var_cost)
    DV.fuel_cost_val = Model.getAttr('x', DV.fuel_cost)
    DV.Xstr_val = DV.Xstr.X
    DV.prod_val = Model.getAttr('x', DV.prod)
    DV.sDis_val = Model.getAttr('x', DV.sDis)
    DV.sLev_val = Model.getAttr('x', DV.sLev)
    DV.sCh_val = Model.getAttr('x', DV.sCh)
    # DV.LL_val = Model.getAttr('x',DV.LL);
    DV.RE_cost_val = Model.getAttr('x', DV.RE_cost)
    # DV.Curtail_val = Model.getAttr('x', DV.Curtail)
    # get costs
    DV.total_cost_val = DV.total_cost.X
    DV.strg_inv_cost_val = DV.strg_inv_cost.X
    # DV.lost_load_cost_val = DV.lost_load_cost.X;
    # DV.curtail_cost_val = DV.curtail_cost.X

def print_results(dat, Setting, stime, Model):
    prod_value = np.zeros((nPlt, nT))
    load_value = np.zeros((nPlt, nT))
    for p in range(nPlt):
        for t in range(nT):
            prod_value[p, t] = DV.prod_val[p, t]
            load_value[p, t] = DV.load_val[p, t]
    total_load = dat.demand.sum()/nYear
    current_path = os.getcwd()
    DF = pd.DataFrame(data={'num_periods': nT,
                            'num_vars': Model.NumVars,
                            'num_constrs': Model.NumConstrs,
                            'Sol_time': np.round(time.time()-stime),
                            'total_cost': DV.total_cost_val,
                            'total_cost_strg': DV.strg_inv_cost_val,
                            'prod_strg': DV.sDis_val.sum()/nYear,
                            'capacity_strg': DV.Xstr_val,
                            'LL_cost': 0,
                            'curtail_cost': 0,
                            'total_LL': 0,
                            'total_Curtail': (prod_value.sum()-load_value.sum())/nYear,
                            'year_list': str(Setting.sub_year_list),  # '
                            'num_yr': Setting.num_y,
                            'ens_id':Setting.ens_id,
                            'weather_model': Setting.weather_model,
                            'wake_allowd': Setting.wake,
                            'landres_allowed': Setting.landr,
                            'total_load': total_load,
                            'LCOE': DV.total_cost_val/(total_load*1000)}, index=[0])
    for dpland in Setting.gas_plant_types:
        dindex = Setting.gas_plant_types.index(dpland)
        pindex = Setting.plant_types.index(dpland)
        DF[f'inv_cost_{dpland}'] = DV.gas_inv_cost_val[dindex]
        DF[f'fuel_cost_{dpland}'] = DV.fuel_cost_val[dindex]
        DF[f'var_cost_{dpland}'] = DV.var_cost_val[dindex]
        DF[f'prod_{dpland}'] = prod_value[pindex, :].sum()/nYear
        DF[f'capacity_{dpland}'] = DV.Xg_val[dindex]
        DF[f'load_{dpland}'] = load_value[pindex, :].sum()/nYear
        DF[f'total_cost_{dpland}'] = DV.gas_inv_cost_val[dindex] + \
            DV.fuel_cost_val[dindex]+DV.var_cost_val[dindex]
        DF[f'upper_bound_{dpland}'] = Setting.UB_dispatchable_cap[dpland]

    for repland in Setting.RE_plant_types:
        rindex = Setting.RE_plant_types.index(repland)
        pindex = Setting.plant_types.index(repland)
        DF[f'inv_cost_{repland}'] = DV.RE_cost_val[rindex]
        DF[f'prod_{repland}'] = prod_value[pindex, :].sum()/nYear
        DF[f'capacity_{repland}'] = DV.Xr_val[rindex].sum()
        DF[f'cell_size_{repland}'] = Setting.RE_cell_size[repland]
        DF[f'load_{repland}'] = load_value[pindex, :].sum()/nYear
        DF[f'total_cost_{repland}'] = DV.RE_cost_val[rindex]
    dfvfile = f'{current_path}/Results/{Setting.test_name}_{Setting.weather_model}_General_Results.csv'
    if not os.path.exists(dfvfile):
        DF.to_csv(dfvfile, mode='w', header=True, index=False)
    else:
        DF.to_csv(dfvfile, mode='a', header=False, index=False)

    if Setting.print_detailed_results == 1:
        for repland in Setting.RE_plant_types:
            rindex = Setting.RE_plant_types.index(repland)
            RE_Xr_val = np.array([])
            RE_Xr_val = [DV.Xr[rindex][n].X for n in range(
                RE_nlocations[rindex])]
            RE_Xr_val = np.array(RE_Xr_val)
            lat = dat.REPlants[rindex].lat[RE_Xr_val != 0]
            lon = dat.REPlants[rindex].lon[RE_Xr_val != 0]
            capacity = RE_Xr_val[RE_Xr_val != 0]
            dfw = pd.DataFrame(
                data={'lat': lat, 'lon': lon, 'capacity': capacity})
            csvfilename_suffix = '%s/Results/%s_sub%dyrs_ens%d_ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s' % (current_path, Setting.test_name, Setting.num_y, Setting.ens_id,
                                                                                                                                    Setting.UB_dispatchable_cap['ng']*100,
                                                                                                                                    Setting.UB_dispatchable_cap['CCGT']*100,
                                                                                                                                    Setting.wake, Setting.landr,
                                                                                                                                    Setting.RE_cell_size['wind-onshore'],
                                                                                                                                    Setting.RE_cell_size['solar-UPV'],
                                                                                                                                    Setting.weather_model)
            dfw.to_csv(csvfilename_suffix+f'_{repland}_locations.csv', encoding='utf-8', index=False)
        DF_prod = pd.DataFrame()
        for plant in Setting.plant_types:
            pindex = Setting.plant_types.index(plant)
            DF_prod[f'prod_{plant}'] = prod_value[pindex, :].squeeze()
            DF_prod[f'load_{plant}'] = load_value[pindex, :].squeeze()
        DF_prod['sLev'] = DV.sLev_val
        DF_prod['sCh'] = DV.sCh_val
        DF_prod['sDis'] = DV.sDis_val
        DF_prod['demand'] = dat.demand
        DF_prod.to_csv(csvfilename_suffix+'_Load.csv', encoding='utf-8', index=False)
