import NCDataCost_multi as NCDataCost
import Modules_cost_multi as Modules
import gurobipy as gp
import gurobipy as gp
from gurobipy import GRB
import time

def runmodel(Setting, mdl, wake, landr, onwindsize, solarsize, cap_ng, cap_cc, sub_year_list, ens_id):
    Setting.num_y = len(sub_year_list)
    Setting.sub_year_list = sub_year_list
    Setting.ens_id = ens_id

    # GW to MW 
    Setting.UB_dispatchable_cap['ng'] = cap_ng
    Setting.UB_dispatchable_cap['CCGT'] = cap_cc  # GW to MW
    Setting.weather_model = mdl
    Setting.wake = wake
    Setting.landr = landr
    Setting.RE_cell_size['wind-onshore'] = onwindsize
    Setting.RE_cell_size['solar-UPV'] = solarsize

    if Setting.wake == 1:
        if Setting.weather_model == "WRHigh":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/wakecf/WTK_wakecf64_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)
        elif Setting.weather_model == "WRLow":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/wakecf/ERA5_wakecf16_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)
    else:
        if Setting.weather_model == "WRHigh":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/simplecf/WTK_simplecf_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)
        elif Setting.weather_model == "WRLow":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/simplecf/ERA5_simplecf_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)

    if Setting.weather_model == "WRHigh":
        Setting.REfile['solar-UPV'] = '%s/%s/Solar/NSRDB_SAM_UTC_%.2f_cf_' % (Setting.datadir, mdl,solarsize)
    else:
        Setting.REfile['solar-UPV'] = '%s/%s/Solar/ERA5_SAM_UTC_%.2f_cf_' % (Setting.datadir, mdl, solarsize)


    Setting.landusefile['solar-UPV'] = '../Landuse_data/wind_coe_composite_50_ISNE_%.2fmean.nc' % (solarsize)
    Setting.landusefile['wind-onshore'] = '../Landuse_data/wind_coe_composite_50_ISNE_%.2fmean.nc' % (onwindsize)

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
    Modules.get_DV_vals(Model, Setting)
    Modules.print_results(dat, Setting, stime, Model)
    Model.reset()
    del (Model)
