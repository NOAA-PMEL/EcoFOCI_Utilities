#!/usr/bin/env python

"""
 NetCDF_EPIC_MakeMissing.py

 History:
 --------
 2016-07-25: update EPIC to CF time routines to be in EPIC2Datetime.py and removed time calls
    in this routine.

 2016-08-10: transfer routine to EcoFOCI_MooringAnalysis package to simplify and unify

"""

#System Stack
import datetime
import argparse

#User Stack
from calc.EPIC2Datetime import EPIC2Datetime, get_UDUNITS
from io_utils.EcoFOCI_netCDF_read import EcoFOCI_netCDF

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2014, 05, 22)
__modified__ = datetime.datetime(2016, 8, 10)
__version__  = "0.2.0"
__status__   = "Development"
__keywords__ = 'netCDF','meta','header', 'csv'

parser = argparse.ArgumentParser(description='Make EPIC Parameter in given file 1e35')
parser.add_argument('ncfile', metavar='ncfile', type=str, help='input file path')
parser.add_argument("-EPIC",'--epic', nargs='+', type=str, help='list of desired epic variables')


args = parser.parse_args()

df = EcoFOCI_netCDF(args.ncfile)
global_atts = df.get_global_atts()
nchandle = df._getnchandle_()
vars_dic = df.get_vars()
ncdata = df.ncreadfile_dic()

for EPIC_var in args.epic:
	try:
		nchandle.variables[EPIC_var][0,:,0,0] = (nchandle.variables[EPIC_var][0,:,0,0] * 0 ) +1e35
		edithist = "{EPIC_var} made missing".format(EPIC_var=EPIC_var)

		print "adding history attribute"
		if not 'History' in global_atts.keys():
		    histtime=datetime.datetime.utcnow()
		    nchandle.setncattr('History','{histtime:%B %d, %Y %H:%M} UTC - {history} '.format(histtime=histtime,history=edithist))
		else:
		    histtime=datetime.datetime.utcnow()
		    nchandle.setncattr('History', global_atts['History'] +'\n'+ '{histtime:%B %d, %Y %H:%M} UTC - {history}'.format(histtime=histtime,history=edithist))

	except:
		print("EPIC Key: {ek} not found".format(ek=EPIC_var))

df.close()