#!/usr/bin/env python

"""
 FOCI_EPIC2CF.py

 Purpose:
 --------

 Check archived netcdf files (often in EPIC format) for needed updates to make CF
  compliant.  Add known or provided information when specified

 History:
 --------
 2017-09-19: 
"""

#System Stack
import datetime
import argparse

#User Stack
from calc.EPIC2Datetime import EPIC2Datetime, get_UDUNITS
from io_utils.EcoFOCI_netCDF_read import EcoFOCI_netCDF

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2017, 9, 17)
__modified__ = datetime.datetime(2017, 9, 17)
__version__  = "0.1.0"
__status__   = "Development"
__keywords__ = 'netCDF','meta','header', 'epic'

parser = argparse.ArgumentParser(description='Process EPIC nc files to make CF compliant ones')
parser.add_argument('ncfile', metavar='ncfile', type=str, help='input file path')
parser.add_argument('operation', metavar='operation', type=str,
			   help='"CF_Convert", "RoundTime" to nearest hour, "Interpolate" to nearest hour, Add "Offset"')
parser.add_argument('-is2D','--is2D', action="store_true",
			   help='convert files like ADCP that have two varying dimensions')

args = parser.parse_args()


if args.operation in ['CF','CF Convert','CF_Convert']:
	#generates near file
	if args.is2D:

		df = EcoFOCI_netCDF( args.sourcefile )
		global_atts = df.get_global_atts()
		vars_dic = df.get_vars()
		ncdata = df.ncreadfile_dic()

		#Convert two word EPIC time to python datetime.datetime representation and then format for CF standards
		dt_from_epic =  EPIC2Datetime(ncdata['time'], ncdata['time2'])
		if args.time_since_str:
			time_since_str = " ".join(args.time_since_str)
			CF_time = get_UDUNITS(dt_from_epic,time_since_str)
		else:
			time_since_str = 'days since 1900-01-01'
			CF_time = get_UDUNITS(dt_from_epic,time_since_str)

		try:
			History=global_atts['History']
		except:
			History=''
		
		###build/copy attributes and fill if empty
		try:
			data_cmnt = global_atts['DATA_CMNT']
		except:
			data_cmnt = ''

		ncinstance = CF_NC_2D(savefile=args.sourcefile.split('.nc')[0] + '.cf.nc')
		ncinstance.file_create()
		ncinstance.sbeglobal_atts(raw_data_file=data_cmnt, Station_Name=global_atts['MOORING'], 
										Water_Depth=global_atts['WATER_DEPTH'], Inst_Type=global_atts['INST_TYPE'],
										Water_Mass=global_atts['WATER_MASS'], Experiment=global_atts['EXPERIMENT'], Project=global_atts['PROJECT'], 
										History=History)
		ncinstance.dimension_init(time_len=len(CF_time),depth_len=len(ncdata['depth']))
		ncinstance.variable_init(df,time_since_str)
		try:
			ncinstance.add_coord_data(depth=ncdata['depth'], latitude=ncdata['lat'], longitude=ncdata['lon'],
											 time=CF_time)
		except KeyError:
			ncinstance.add_coord_data(depth=ncdata['depth'], latitude=ncdata['latitude'], longitude=ncdata['longitude'],
											 time=CF_time)

		ncinstance.add_data(ncdata)
		ncinstance.add_history('EPIC two time-word key converted to udunits')
		ncinstance.close()
		df.close()

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