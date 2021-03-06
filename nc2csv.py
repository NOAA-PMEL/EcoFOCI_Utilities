#!/usr/bin/env python

"""
 Background:
 ===========
 nc2csv.py

  Purpose:
 ========
 Convert timeseries and ctd netcdf files into csv files


 File Format:
 ============
 - S.Bell - epic ctd and epic nut data 


 History:
 ========
 2020-12-21: IPHC specific ctd output
 2020-03-26: EPIC time conversion modified to support python3
 2018-07-24: replace print statements with functions and import future for py3 compatability
 2016-07-25: update EPIC to CF time routines to be in EPIC2Datetime.py and removed time calls
    in this routine.

 2016-08-10: transfer routine to EcoFOCI_MooringAnalysis package to simplify and unify


 Compatibility:
 ==============
 python >=3.7 ** tested
 python 2.7 ** tested but no longer developed for
"""

from __future__ import print_function

# System Stack
import datetime
import os, sys
import argparse

# Science Stack
from netCDF4 import Dataset, date2num
import numpy as np
import pandas as pd

# User Stack
from io_utils import ConfigParserLocal
from calc.EPIC2Datetime import EPIC2Datetime, get_UDUNITS
from io_utils.EcoFOCI_netCDF_read import EcoFOCI_netCDF

__author__ = "Shaun Bell"
__email__ = "shaun.bell@noaa.gov"
__created__ = datetime.datetime(2014, 5, 22)
__modified__ = datetime.datetime(2016, 8, 10)
__version__ = "0.2.0"
__status__ = "Development"
__keywords__ = "netCDF", "meta", "header", "csv"

"""---------------------------------- Main --------------------------------------------"""

parser = argparse.ArgumentParser(description="Convert .nc to .csv screen output")
parser.add_argument("infile", metavar="infile", type=str, help="input file path")
parser.add_argument(
    "-p", "--PointerFile", type=str, help="provide a pointer file ::TIMESERIES ONLY::"
)
parser.add_argument("-ctd", "--ctd", action="store_true", help="For CTD profiles")
parser.add_argument(
    "-timeseries", "--timeseries", action="store_true", help="For timeseries profiles"
)
parser.add_argument(
    "-header_meta",
    "--header_meta",
    action="store_true",
    help="Add header meta information from nc attributes",
)
parser.add_argument(
    "-units_meta",
    "--units_meta",
    action="store_true",
    help="Add ctd identifying info from nc attributes to columns",
)
parser.add_argument(
    "-sorted", "--sorted", action="store_true", help="sort input files by alpha"
)
parser.add_argument(
    "-non_epic", "--non_epic", action="store_true", help="non_epic time files"
)
parser.add_argument(
    "-IPHC", "--IPHC", action="store_true", help="list of desired epic variables"
)
parser.add_argument(
    "-EPIC", "--epic", nargs="+", type=str, help="list of desired epic variables"
)

parser.add_argument(
    "-subset",
    "--subset",
    type=int,
    help="hour (in 24hour format) to subset data for e.g. 12 gives noon value only ::TIMESERIES:: only",
)
parser.add_argument(
    "-hd",
    "--hourly_decimate",
    action="store_true",
    help="decimate data to hourly ::TIMESERIES ONLY::",
)
parser.add_argument(
    "-tmd",
    "--ten_minute_decimate",
    action="store_true",
    help="decimate data to every ten minutes ::TIMESERIES:: only",
)
parser.add_argument(
    "-dave",
    "--daily_average",
    action="store_true",
    help="generate daily max/min/mean data ::TIMESERIES:: only and uses pointerfile",
)
parser.add_argument(
    "-mave",
    "--monthly_average",
    action="store_true",
    help="generate monthly mean data ::TIMESERIES:: only and uses pointerfile",
)

args = parser.parse_args()

if args.timeseries and args.PointerFile:

    """-------------------------------------------------------------------------
    Get parameters from specified pointerfile - 
    an example is shown in the header description of
    this program.  It can be of the .pyini (json) form or .yaml form

    """
    if args.PointerFile.split(".")[-1] == "pyini":
        pointer_file = ConfigParserLocal.get_config(args.PointerFile, "json")
    elif args.PointerFile.split(".")[-1] == "yaml":
        pointer_file = ConfigParserLocal.get_config(args.PointerFile, "yaml")
    else:
        print("PointerFile format not recognized")
        sys.exit()

    MooringDataPath = pointer_file["mooring_data_path"]
    files = pointer_file["mooring_files"]
    files_path = [a + b for a, b in zip(MooringDataPath, files)]

    data_var = [pointer_file["EPIC_Key"][0]]

    if args.sorted:
        files_path = sorted(files_path)

    if args.daily_average:

        for ind, ncfile in enumerate(files_path):

            ###nc readin/out
            df = EcoFOCI_netCDF(ncfile)
            global_atts = df.get_global_atts()
            vars_dic = df.get_vars()
            data = df.ncreadfile_dic()
            df.close()

            nctime = EPIC2Datetime(data["time"], data["time2"])
            pddata = pd.DataFrame(data[data_var[0]][:, 0, 0, 0], index=nctime)

            df = pddata.resample("D").mean()
            # df['max'] = pddata.resample('D').max()
            # df['min'] = pddata.resample('D').min()

            print(ncfile)
            print(df.to_csv())

    elif args.monthly_average:

        for ind, ncfile in enumerate(files_path):

            ###nc readin/out
            df = EcoFOCI_netCDF(ncfile)
            global_atts = df.get_global_atts()
            vars_dic = df.get_vars()
            data = df.ncreadfile_dic()
            df.close()

            nctime = EPIC2Datetime(data["time"], data["time2"])
            try:
                pddata = pd.DataFrame(data[data_var[0]][:, 0, 0, 0], index=nctime)
            except:
                print(
                    "Variable not found in file - skipping {ncfile}".format(
                        ncfile=ncfile
                    )
                )
                continue
            pddata = pddata.replace(1e35, np.nan)
            pddata[pddata > 1e34] = np.nan

            df = pddata.resample("M").mean()

            print(ncfile)
            print(df.to_csv())
    else:
        for ind, ncfile in enumerate(files_path):

            ###nc readin/out
            df = EcoFOCI_netCDF(ncfile)
            global_atts = df.get_global_atts()
            vars_dic = df.get_vars()
            data = df.ncreadfile_dic()
            ### get and print epic timeseries data
            # header
            header = "time, "
            for k in sorted(vars_dic.keys()):
                if k in data_var:
                    header = header + ", " + k
            print(header + ", index")

            if args.units_meta:

                # units/var attributes
                longname = ", "
                header = "time, "
                for v, k in enumerate(sorted(vars_dic)):
                    if k in data_var:
                        tmp = df.get_vars_attributes(var_name=k)
                        header = header + ", " + tmp.units
                        try:
                            longname = longname + ", " + tmp.long_name
                        except:
                            longname = longname + ", "

                print(longname)
                print(header + ", index")

            for i, val in enumerate(data["time"]):

                if args.subset:
                    if (
                        EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0]
                    ).hour == args.subset:
                        timestr = datetime.datetime.strftime(
                            EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                            "%Y-%m-%d %H:%M:%S",
                        )
                        line = ""
                        for k in sorted(vars_dic.keys()):
                            if k in ["time", "time2"]:
                                pass
                            elif k in data_var:
                                if data[k][i, 0, 0, 0] >= 1e34:
                                    line = line + ","
                                else:
                                    line = line + ", " + str(data[k][i, 0, 0, 0])
                        print(timestr + ", " + line + ", " + str(i))
                else:
                    timestr = datetime.datetime.strftime(
                        EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                        "%Y-%m-%d %H:%M:%S",
                    )
                    line = ""
                    for k in sorted(vars_dic.keys()):
                        if k in ["time", "time2"]:
                            pass
                        elif k in data_var:
                            if data[k][i, 0, 0, 0] >= 1e34:
                                line = line + ","
                            else:
                                line = line + ", " + str(data[k][i, 0, 0, 0])
                    print(timestr + ", " + line + ", " + str(i))
            df.close()

elif not args.timeseries and args.PointerFile:
    print("Only capable of dealing with timeseries pointer files")

else:
    ###nc readin/out
    ncfile = args.infile
    df = EcoFOCI_netCDF(ncfile)
    global_atts = df.get_global_atts()
    vars_dic = df.get_vars()
    data = df.ncreadfile_dic()

    if args.header_meta:
        ### get and print epic header information
        print("Global Attributes: for file {0}".format(args.infile.split("/")[-1]))
        for var in global_atts.keys():
            try:
                print("            {0}: {1}".format(var, global_atts[var]))
            except UnicodeEncodeError:
                print(
                    "            {0}: {1}".format(
                        var, "***Unrecognized ASCII characters***"
                    )
                )
        print("\n")

    if args.hourly_decimate:
        for i, val in enumerate(data["time"]):
            if (EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0]).minute == 0:
                timestr = datetime.datetime.strftime(
                    EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                    "%Y-%m-%d %H:%M:%S",
                )
                line = ""
                for k in sorted(vars_dic.keys()):
                    if k in ["time", "time2"]:
                        pass
                    elif k in [
                        "lat",
                        "lon",
                        "dep",
                        "depth",
                        "depth01",
                        "latitude",
                        "longitude",
                    ]:
                        line = line + ", " + str(data[k][0])
                    else:
                        line = line + ", " + str(data[k][i, 0, 0, 0])

                print(timestr + ", " + line)

    if args.ten_minute_decimate:
        for i, val in enumerate(data["time"]):
            if (
                (EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0]).minute
            ) % 10 == 0:
                timestr = datetime.datetime.strftime(
                    EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                    "%Y-%m-%d %H:%M:%S",
                )
                line = ""
                for k in sorted(vars_dic.keys()):
                    if k in ["time", "time2"]:
                        pass
                    elif k in [
                        "lat",
                        "lon",
                        "dep",
                        "depth",
                        "depth01",
                        "latitude",
                        "longitude",
                    ]:
                        line = line + ", " + str(data[k][0])
                    else:
                        line = line + ", " + str(data[k][i, 0, 0, 0])

                print(timestr + ", " + line)

    if args.timeseries and not args.epic:
        ### get and print epic timeseries data
        # header
        if args.units_meta:
            header = "time, "
            for k in sorted(vars_dic.keys()):
                if (k != "time") and (k != "time2"):
                    header = header + ", " + k
            print(header)

            # units/var attributes
            longname = ", "
            header = "time, "
            for v, k in enumerate(sorted(vars_dic)):
                if (k != "time") and (k != "time2"):
                    tmp = df.get_vars_attributes(var_name=k)
                    header = header + ", " + tmp.units
                    try:
                        longname = longname + ", " + tmp.long_name
                    except:
                        longname = longname + ", "

            print(longname)
            print(header)

        for i, val in enumerate(data["time"]):
            if args.subset:
                if (
                    EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0]
                ).hour == args.subset:
                    timestr = datetime.datetime.strftime(
                        EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                        "%Y-%m-%d %H:%M:%S",
                    )
                    line = ""
                    for k in sorted(vars_dic.keys()):
                        if k in ["time", "time2"]:
                            pass
                        elif k in ["lat", "lon", "latitude", "longitude"]:
                            line = line + ", " + str(data[k][0])
                        elif k in ["dep", "depth", "depth01"]:
                            line = line + ", " + str(data[k][0])
                        else:
                            line = line + ", " + str(data[k][i, 0, 0, 0])

                    print(timestr + ", " + line)
            else:
                timestr = datetime.datetime.strftime(
                    EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                    "%Y-%m-%d %H:%M:%S",
                )
                line = ""
                for k in sorted(vars_dic.keys()):
                    if k in ["time", "time2"]:
                        pass
                    elif k in ["lat", "lon", "latitude", "longitude"]:
                        line = line + ", " + str(data[k][0])
                    elif k in ["dep", "depth", "depth01"]:
                        line = line + ", " + str(data[k][0])
                    else:
                        line = line + ", " + str(data[k][i, 0, 0, 0])

                print(timestr + ", " + line)

    if args.timeseries and args.epic:

        ### get and print epic timeseries data
        # header

        header = "time, "
        for k in sorted(vars_dic.keys()):
            if k in args.epic:
                header = header + ", " + k
        print(header + ", index")

        if args.units_meta:

            # units/var attributes
            longname = ", "
            header = "time, "
            for k in sorted(vars_dic.keys()):
                if k in args.epic:
                    tmp = df.get_vars_attributes(var_name=k)
                    header = header + ", " + tmp.units
                    try:
                        longname = longname + ", " + tmp.long_name
                    except:
                        longname = longname + ", "

            print(longname)
            print(header + ", index")

        for i, val in enumerate(data["time"]):

            if args.subset:
                if (
                    EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0]
                ).hour == args.subset:
                    timestr = datetime.datetime.strftime(
                        EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                        "%Y-%m-%d %H:%M:%S",
                    )
                    line = ""
                    for k in sorted(vars_dic.keys()):
                        if k in ["time", "time2"]:
                            pass
                        elif k in args.epic:
                            if data[k][i, 0, 0, 0] >= 1e34:
                                line = line + ","
                            else:
                                line = line + ", " + str(data[k][i, 0, 0, 0])
                    print(timestr + ", " + line + ", " + str(i))
            else:
                timestr = datetime.datetime.strftime(
                    EPIC2Datetime([data["time"][i]], [data["time2"][i]])[0],
                    "%Y-%m-%d %H:%M:%S",
                )
                line = ""
                for k in sorted(vars_dic.keys()):
                    if k in ["time", "time2"]:
                        pass
                    elif k in args.epic:
                        if data[k][i, 0, 0, 0] >= 1e34:
                            line = line + ","
                        else:
                            line = line + ", " + str(data[k][i, 0, 0, 0])
                print(timestr + ", " + line + ", " + str(i))

    if args.ctd and not args.epic:
        ### get and print epic ctd data
        # header
        if args.units_meta:
            header = "cast, time"
            for k in sorted(vars_dic.keys()):
                if (k != "time") and (k != "time2"):
                    header = header + ", " + k
            print(header)

            # units/var attributes
            longname = ", "
            header = "cast, time"
            for v, k in enumerate(sorted(vars_dic)):
                if (k != "time") and (k != "time2"):
                    tmp = df.get_vars_attributes(var_name=k)
                    header = header + ", " + tmp.units
                    try:
                        longname = longname + ", " + tmp.long_name
                    except:
                        longname = longname + ", "

            print(longname)
            print(header)

        vert_var = ""
        for param in ["dep", "depth", "pressure"]:
            if not len(vert_var) > 0:
                vert_var = data.get(param, "")

        try:
            vert_var
        except:
            "No recognized depth parameter"

        for i, val in enumerate(vert_var):
            timestr = datetime.datetime.strftime(
                EPIC2Datetime([data["time"][0]], [data["time2"][0]])[0],
                "%Y-%m-%d %H:%M:%S",
            )
            line = ""
            for k in sorted(vars_dic.keys()):
                if k in ["time", "time2"]:
                    pass
                elif k in ["lat", "lon", "latitude", "longitude", "time01", "time012"]:
                    line = line + ", " + str(data[k][0])
                elif k in ["depth", "dep", "pressure"]:
                    line = line + ", " + str(data[k][i])
                else:
                    line = line + ", " + str(data[k][0, i, 0, 0])

            print(global_atts["CAST"] + ", " + timestr + line)

    if args.ctd and args.epic:
        ### get and print epic ctd data
        # header
        if args.units_meta:
            header = "cast, time (utc)"
            for k in sorted(vars_dic.keys()):
                if k in ["time", "time2"]:
                    pass
                elif k in ["lat", "lon", "latitude", "longitude", "time01", "time012"]:
                    header = header + ", " + k
                elif k in ["depth", "dep", "pressure"]:
                    header = header + ", " + k
                elif k in args.epic:
                    header = header + ", " + k
            print(header)

            # units/var attributes
            longname = ", "
            header = "cast, time (utc)"
            for v, k in enumerate(sorted(vars_dic)):
                if k in ["time", "time2"]:
                    pass
                elif k in ["lat", "lon", "latitude", "longitude", "time01", "time012"]:
                    tmp = df.get_vars_attributes(var_name=k)
                    header = header + ", " + tmp.units
                    try:
                        longname = longname + ", " + tmp.long_name
                    except:
                        longname = longname + ", "
                elif k in ["depth", "dep", "pressure"]:
                    tmp = df.get_vars_attributes(var_name=k)
                    header = header + ", " + tmp.units
                    try:
                        longname = longname + ", " + tmp.long_name
                    except:
                        longname = longname + ", "
                elif k in args.epic:
                    tmp = df.get_vars_attributes(var_name=k)
                    header = header + ", " + tmp.units
                    try:
                        longname = longname + ", " + tmp.long_name
                    except:
                        longname = longname + ", "

            print(longname)
            print(header)

        vert_var = ""
        for param in ["dep", "depth", "pressure"]:
            if not len(vert_var) > 0:
                vert_var = data.get(param, "")

        try:
            vert_var
        except:
            "No recognized depth parameter"

        for i, val in enumerate(vert_var):
            timestr = datetime.datetime.strftime(
                EPIC2Datetime([data["time"][0]], [data["time2"][0]])[0],
                "%Y-%m-%d %H:%M:%S",
            )
            line = ""
            for k in sorted(vars_dic.keys()):
                if k in ["time", "time2"]:
                    pass
                elif k in ["lat", "lon", "latitude", "longitude", "time01", "time012"]:
                    line = line + ", " + str(data[k][0])
                elif k in ["depth", "dep", "pressure"]:
                    line = line + ", " + str(data[k][i])
                elif k in args.epic:
                    line = line + ", " + str(data[k][0, i, 0, 0])

            print(global_atts["CAST"] + ", " + timestr + line)

    df.close()

if args.non_epic:
    ### get and print epic timeseries data
    header = ""
    for k in sorted(vars_dic.keys()):
        header = header + ", " + k
    print(header)

    # units/var attributes
    longname = ", "
    for v, k in enumerate(sorted(vars_dic)):
        tmp = df.get_vars_attributes(var_name=k)
        try:
            longname = longname + ", " + tmp.long_name
        except:
            longname = longname + ", "

    print(longname)
    print(header)

    for i, val in enumerate(data["N_LEVELS"]):
        line = ""
        for k in sorted(vars_dic.keys()):
            line = line + ", " + str(data[k][i, 0, 0, 0])

        print(timestr + ", " + line)

if args.IPHC:
    ###nc readin/out
    ncfile = args.infile
    df = EcoFOCI_netCDF(ncfile)
    global_atts = df.get_global_atts()
    vars_dic = df.get_vars()
    data = df.ncreadfile_dic()
    ### get and print epic ctd data

    cast = (args.infile).split('/')[-1][3:6]
    # header

    header = "Year, Latitude(Deg), Longitude(Deg), Station, VesselCode, Cast, WaterDepth(m), CastDate, Pressure(db)"
    for k in (args.epic):
        if k in ["time", "time2"]:
            pass
        elif k in ["lat", "lon", "latitude", "longitude", "time01", "time012"]:
            pass
        elif k in ["depth", "dep", "pressure"]:
            pass
        elif k in args.epic:
            if k == 'T_28':
                header = header + ", " + 'Temperature(C)'
            if k == 'S_41':
                header = header + ", " + 'Salinity'
            if k == 'Chl_933':
                header = header + ", " + 'Chlorophyll'
            if k == 'pH_159':
                header = header + ", " + 'pH'
            if k == 'O_60':
                header = header + ", " + 'Oxygen(ML/L)'            
            if k == 'OST_62':
                header = header + ", " + 'Oxygen(%Saturation)'
            if k == 'O_65':
                header = header + ", " + 'Oxygen(microMol/kg)'
            if k == 'ST_70':
                header = header + ", " + 'Sigma-T(kg/m**3)'
    print(header)

    

    vert_var = ""
    for param in ["dep", "depth", "pressure"]:
        if not len(vert_var) > 0:
            vert_var = data.get(param, "")

    try:
        vert_var
    except:
        "No recognized depth parameter"

    for i, val in enumerate(vert_var):
        timestr = datetime.datetime.strftime(
            EPIC2Datetime([data["time"][0]], [data["time2"][0]])[0],
            "%d-%b-%Y",
        )
        timestr_year = datetime.datetime.strftime(
            EPIC2Datetime([data["time"][0]], [data["time2"][0]])[0],
            "%Y",
        )

        line = ""
        for k in (args.epic):
            if k in ["time", "time2"]:
                pass
            elif k in ["lat", "latitude", "time01", "time012"]:
                pass
            elif k in ["longitude", "lon"]:
                pass
            elif k in ["depth", "dep", "pressure"]:
                pass
            elif k in args.epic:
                if (data[k][0, i, 0, 0] > 1e30):
                    line = line + ", " + '99999'
                elif k == 'ST_70':
                    line = line + ", " + "{:5.3f}".format(data[k][0, i, 0, 0])
                else:
                    line = line + ", " + str(data[k][0, i, 0, 0])

        dep_data = ""
        for k in vars_dic.keys():
            if k in ["depth", "dep", "pressure"]:
                dep_data = dep_data + ", " + str(data[k][i])

        loc_data = ""
        for k in vars_dic.keys():
            if k in ["lat", "latitude", "time01", "time012"]:
                loc_data = loc_data + ", " + "{:7.4f}".format(data[k][0])
            elif k in ["longitude", "lon"]:
                loc_data = loc_data + ", " + "{:7.4f}".format(-1* data[k][0])

        print(timestr_year + loc_data + ", " + global_atts["STNNO"] + ", " + global_atts["VSLCDE"] + ", " + cast + ", "  + "{:4.0f}".format(global_atts["WATER_DEPTH"]) + ", " + timestr + dep_data + line)

    df.close()