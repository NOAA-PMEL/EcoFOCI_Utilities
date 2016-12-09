#!/usr/bin/env python

"""
 nc2csv.py

 History:
 --------
 2016-07-25: update EPIC to CF time routines to be in EPIC2Datetime.py and removed time calls
    in this routine.

 2016-08-10: transfer routine to EcoFOCI_MooringAnalysis package to simplify and unify

"""

#System Stack
import datetime
import os
import argparse

#Science Stack
from netCDF4 import Dataset, date2num
import numpy as np

#User Stack
from calc.EPIC2Datetime import EPIC2Datetime
from io_utils.EcoFOCI_netCDF_read import EcoFOCI_netCDF

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2014, 05, 22)
__modified__ = datetime.datetime(2016, 8, 10)
__version__  = "0.2.0"
__status__   = "Development"
__keywords__ = 'netCDF','meta','header', 'csv'

"""---------------------------------- Main --------------------------------------------"""

parser = argparse.ArgumentParser(description='Convert .nc to .csv screen output')
parser.add_argument('infile', metavar='infile', type=str, help='input file path')
parser.add_argument("-ctd", '--ctd', action="store_true", help='For CTD profiles')
parser.add_argument("-timeseries", '--timeseries', action="store_true", help='For timeseries profiles')
parser.add_argument("-header_meta", '--header_meta', action="store_true", help='Add header meta information from nc attributes')
parser.add_argument("-units_meta", '--units_meta', action="store_true", help='Add ctd identifying info from nc attributes to columns')
parser.add_argument("-EPIC",'--epic', nargs='+', type=str, help='list of desired epic variables')
parser.add_argument("-subset",'--subset', type=int, 
        help='hour (in 24hour format) to subset data for e.g. 12 gives noon value only ::TIMESERIES:: only')
parser.add_argument("-hd",'--hourly_decimate', action="store_true", 
        help='decimate data to hourly ::TIMESERIES:: only')
parser.add_argument("-tmd",'--ten_minute_decimate', action="store_true", 
        help='decimate data to every ten minutes ::TIMESERIES:: only')
args = parser.parse_args()


###nc readin/out
ncfile = args.infile
df = EcoFOCI_netCDF(ncfile)
global_atts = df.get_global_atts()
vars_dic = df.get_vars()
data = df.ncreadfile_dic()

if args.header_meta:
    ### get and print epic header information
    print "Global Attributes: for file {0}".format(args.infile.split('/')[-1])
    for var in global_atts.keys():
        try:
            print ("            {0}: {1}").format(var,global_atts[var])
        except UnicodeEncodeError:
            print ("            {0}: {1}").format(var,'***Unrecognized ASCII characters***')            
    print "\n"

if args.hourly_decimate:
    for i, val in enumerate(data['time']):
            if (EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0]).minute == 0:
                timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0],"%Y-%m-%d %H:%M:%S" )
                line = ''
                for k in vars_dic.keys():
                    if k in ['time','time2']:
                        pass
                    elif k in ['lat','lon','dep','depth','depth01','latitude','longitude']:
                        line = line + ', ' + str(data[k][0])
                    else:
                        line = line + ', ' + str(data[k][i,3,0,0])
                    
                print timestr + ', ' + line

if args.ten_minute_decimate:
    for i, val in enumerate(data['time']):
            if ((EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0]).minute) % 10 == 0:
                timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0],"%Y-%m-%d %H:%M:%S" )
                line = ''
                for k in vars_dic.keys():
                    if k in ['time','time2']:
                        pass
                    elif k in ['lat','lon','dep','depth','depth01','latitude','longitude']:
                        line = line + ', ' + str(data[k][0])
                    else:
                        line = line + ', ' + str(data[k][i,3,0,0])
                    
                print timestr + ', ' + line
    
if args.timeseries and not args.epic:
    ### get and print epic timeseries data
    #header
    if args.units_meta:
        header = 'time, '
        for k in vars_dic.keys():
            if (k != 'time') and (k != 'time2'):
                header = header + ', ' + k
        print header
    
        #units/var attributes
        longname = ', '
        header = 'time, '
        for v, k in enumerate(vars_dic):
            if (k != 'time') and (k != 'time2'):
                tmp = df.get_vars_attributes(var_name=k)
                header = header + ', ' + tmp.units
                try:
                    longname = longname + ', ' + tmp.long_name
                except:
                    longname = longname + ', '

        print longname
        print header


    for i, val in enumerate(data['time']):
        if args.subset:
            if (EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0]).hour == args.subset:
                timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0],"%Y-%m-%d %H:%M:%S" )
                line = ''
                for k in vars_dic.keys():
                    if k in ['time','time2']:
                        pass
                    elif k in ['lat','lon','latitude','longitude']:
                        line = line + ', ' + str(data[k][0])
                    elif k in ['dep','depth','depth01']:
                        line = line + ', ' + str(data[k][3])
                    else:
                        line = line + ', ' + str(data[k][i,3,0,0])
                    
                print timestr + ', ' + line
        else:
            timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0],"%Y-%m-%d %H:%M:%S" )
            line = ''
            for k in vars_dic.keys():
                if k in ['time','time2']:
                    pass
                elif k in ['lat','lon','latitude','longitude']:
                    line = line + ', ' + str(data[k][0])
                elif k in ['dep','depth','depth01']:
                    line = line + ', ' + str(data[k][3])
                else:
                    line = line + ', ' + str(data[k][i,3,0,0])
                
            print timestr + ', ' + line

if args.timeseries and args.epic:

    ### get and print epic timeseries data
    #header
    if args.units_meta:
  
        #units/var attributes
        longname = ', '
        header = 'time, '
        for v, k in enumerate(vars_dic):
            if k in args.epic:
                tmp = df.get_vars_attributes(var_name=k)
                header = header + ', ' + tmp.units
                try:
                    longname = longname + ', ' + tmp.long_name
                except:
                    longname = longname + ', '

        print longname
        print header + ', index'

    for i, val in enumerate(data['time']):

        if args.subset:
            if (EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0]).hour == args.subset:
                timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0],"%Y-%m-%d %H:%M:%S" )
                line = ''
                for k in vars_dic.keys():
                    if k in ['time','time2']:
                        pass
                    elif k in args.epic:
                        if (data[k][i,3,0,0] >= 1e34):
                            line = line + ','
                        else:
                            line = line + ', ' + str(data[k][i,3,0,0])
                print timestr + ', ' + line + ', ' + str(i)
        else:
            timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][i],],[data['time2'][i],])[0],"%Y-%m-%d %H:%M:%S" )
            line = ''
            for k in vars_dic.keys():
                if k in ['time','time2']:
                    pass
                elif k in args.epic:
                    if (data[k][i,3,0,0] >= 1e34):
                        line = line + ','
                    else:
                        line = line + ', ' + str(data[k][i,3,0,0])
            print timestr + ', ' + line + ', ' + str(i)

if args.ctd and not args.epic:
    ### get and print epic ctd data
    #header
    if args.units_meta:
        header = 'cast, time'
        for k in vars_dic.keys():
            if (k != 'time') and (k != 'time2'):
                header = header + ', ' + k
        print header
    
        #units/var attributes
        longname = ', '
        header = 'cast, time'
        for v, k in enumerate(vars_dic):
            if (k != 'time') and (k != 'time2'):
                tmp = df.get_vars_attributes(var_name=k)
                header = header + ', ' + tmp.units
                try:
                    longname = longname + ', ' + tmp.long_name
                except:
                    longname = longname + ', '

        print longname
        print header


    try:
        vert_var = data['dep']
    except:
        vert_var = data['depth']

    for i, val in enumerate(vert_var):
        timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][0],], [data['time2'][0],])[0],"%Y-%m-%d %H:%M:%S" )
        line = ''
        for k in vars_dic.keys():
            if k in ['time','time2']:
                pass
            elif k in ['lat','lon','latitude','longitude','time01','time012']:
                line = line + ', ' + str(data[k][0])
            elif k in ['depth','dep']:
                line = line + ', ' + str(data[k][i])
            else:
                line = line + ', ' + str(data[k][0,i,0,0])
            
        print global_atts['CAST'] + ', ' + timestr + line

if args.ctd and args.epic:
    ### get and print epic ctd data
    #header
    if args.units_meta:
        header = 'cast, time (utc)'
        for k in vars_dic.keys():
            if k in ['time','time2']:
                pass
            elif k in ['lat','lon','latitude','longitude','time01','time012']:
                header = header + ', ' + k
            elif k in ['depth','dep']:
                header = header + ', ' + k
            elif k in args.epic:
                header = header + ', ' + k
        print header
    
        #units/var attributes
        longname = ', '
        header = 'cast, time (utc)'
        for v, k in enumerate(vars_dic):
            if k in ['time','time2']:
                pass
            elif k in ['lat','lon','latitude','longitude','time01','time012']:
                tmp = df.get_vars_attributes(var_name=k)
                header = header + ', ' + tmp.units
                try:
                    longname = longname + ', ' + tmp.long_name
                except:
                    longname = longname + ', '
            elif k in ['depth','dep']:
                tmp = df.get_vars_attributes(var_name=k)
                header = header + ', ' + tmp.units
                try:
                    longname = longname + ', ' + tmp.long_name
                except:
                    longname = longname + ', '
            elif k in args.epic:
                tmp = df.get_vars_attributes(var_name=k)
                header = header + ', ' + tmp.units
                try:
                    longname = longname + ', ' + tmp.long_name
                except:
                    longname = longname + ', '

        print longname
        print header


    try:
        vert_var = data['dep']
    except:
        vert_var = data['depth']

    for i, val in enumerate(vert_var):
        timestr = datetime.datetime.strftime(EPIC2Datetime([data['time'][0],], [data['time2'][0],])[0],"%Y-%m-%d %H:%M:%S" )
        line = ''
        for k in vars_dic.keys():
            if k in ['time','time2']:
                pass
            elif k in ['lat','lon','latitude','longitude','time01','time012']:
                line = line + ', ' + str(data[k][0])
            elif k in ['depth','dep']:
                line = line + ', ' + str(data[k][i])
            elif k in args.epic:
                line = line + ', ' + str(data[k][0,i,0,0])
            
        print global_atts['CAST'] + ', ' + timestr + line

df.close()

