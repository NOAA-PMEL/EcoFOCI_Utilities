#!/usr/bin/env python

"""
 Background:
 --------
 EPIC_2Dxlsx2nc.py
 
 
 Purpose:
 --------
 Convert excel .xlsx files into epic netcdf files.  

 Requirements:
 -------------
 Header Row must only include 'time' (str representation as mm/dd/yy hh:mm:ss) and epic variable names

 See EcoFOCI_config/epickkey.json for valid keys but any key can be made up.

 History:
 --------
 2016-12-02: SBELL - Add ctd/profile routines

"""

#System Stack
import os
import sys
import datetime
import argparse

#Science Stack
import numpy as np
import pandas as pd

#User defined Stack
from io_utils.ConfigParserLocal import get_config, get_config_yaml
from io_utils.EcoFOCI_netCDF_write import CF_NC_2D
from calc.EPIC2Datetime import EPIC2Datetime, Datetime2EPIC, get_UDUNITS

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2016, 8, 11)
__modified__ = datetime.datetime(2016, 8, 11)
__version__  = "0.1.0"
__status__   = "Development"
__keywords__ = 'Mooring', 'data','netcdf','epic','excel','xlsx'

"""------------------------- datetime64 --------------------------------------------"""

def dt64todt(dt64):
	return datetime.datetime.utcfromtimestamp((dt64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's'))    


"""--------------------------------main Routines---------------------------------------"""

parser = argparse.ArgumentParser(description='Convert excel data into epic flavored netcdf files with CF times')
parser.add_argument('ExcelDataPath', metavar='ExcelDataPath', type=str, 
               help='full path to excel (.xlsx) data file')
parser.add_argument('OutDataFile', metavar='OutDataFile', type=str, 
               help='full path to output data file')
parser.add_argument('--latlon', nargs=2, type=float, help='latitude, longitude of mooring file')
parser.add_argument('-fill_na','--fill_na', action="store_true", help='fill nan with 1e35')

args = parser.parse_args()

wb_temp = pd.read_excel(args.ExcelDataPath,sheetname='Temperature', na_values=[1E+35,'1E+35',' 1E+35'])
wb_temp.rename(columns=lambda x: x.strip(), inplace=True)
if args.fill_na:
	wb_temp.fillna(1E+35, inplace=True)

wb_pres = pd.read_excel(args.ExcelDataPath,sheetname='Pressure', na_values=[1E+35,'1E+35',' 1E+35'])
wb_pres.rename(columns=lambda x: x.strip(), inplace=True)
if args.fill_na:
	wb_pres.fillna(1E+35, inplace=True)

wb_sal = pd.read_excel(args.ExcelDataPath,sheetname='Salinity', na_values=[1E+35,'1E+35',' 1E+35'])
wb_sal.rename(columns=lambda x: x.strip(), inplace=True)
if args.fill_na:
	wb_sal.fillna(1E+35, inplace=True)

wb_date = pd.read_excel(args.ExcelDataPath,sheetname='DateTime',
						na_values=[1E+35,'1E+35',' 1E+35'],
						parse_dates=[['Date','Time']])

datetime = [dt64todt(x) for x in wb_date.Date_Time.values]
wb_coords = pd.read_excel(args.ExcelDataPath,sheetname='Coords', na_values=[1E+35,'1E+35',' 1E+35'])


EPIC_VARS_dict = get_config_yaml('EcoFOCI_config/epickeys/STP_epickeys.yaml')


#cycle through and build data arrays
#create a "data_dic" and associate the data with an epic key
#this key needs to be defined in the EPIC_VARS dictionary in order to be in the nc file
# if it is defined in the EPIC_VARS dic but not below, it will be filled with missing values
# if it is below but not the epic dic, it will not make it to the nc file
data_dic = {}
data_dic['T_20'] = wb_temp.values
data_dic['S_41'] = wb_sal.values
data_dic['P_1'] = wb_pres.values




if args.latlon:
	(lat,lon) = args.latlon
else:
	(lat,lon) = (-9999, -9999)

ncinstance = CF_NC_2D(savefile=args.OutDataFile)
ncinstance.file_create()
ncinstance.sbeglobal_atts(raw_data_file=args.ExcelDataPath.split('/')[-1])
ncinstance.dimension_init(time_len=len(wb_date.Date_Time.values),depth_len=len(wb_coords.Depth.to_dict().values()))
ncinstance.variable_init(EPIC_VARS_dict)
ncinstance.add_coord_data(depth=wb_coords.Depth.values, latitude=lat, longitude=lon, time=get_UDUNITS(datetime))
ncinstance.add_data(EPIC_VARS_dict,data_dic=data_dic)
ncinstance.close()
