#!/usr/bin/env python

"""
EPIC_DataValidator.py

 Purpose:
 -----

 Utility to check if data meets valid EPIC characteristics for usage with many legacy routines

 Usage:
 ------
 EPIC_DataValidator.py -f {filename} -- reports on a single file
 EPIC_DataValidator.py -d {dirname}  -- reports on all *.nc in a directory

 
 History:
 --------

"""

#System Stack
import datetime
import argparse
import os

#Science Stack
import xarray as xr


__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2016, 11, 12)
__modified__ = datetime.datetime(2016, 11, 12)
__version__  = "0.1.0"
__status__   = "Development"
__keywords__ = 'netCDF','meta','header'

"""---------------------------------- Main --------------------------------------------"""

   
parser = argparse.ArgumentParser(description='Summary of input .nc file.')
parser.add_argument('-i','--infile', type=str,
               help='input file path')
parser.add_argument('-d','--indir', type=str,
               help='input directory')

args = parser.parse_args()

if args.infile:
	###nc readin/out
	with xr.open_dataset(args.infile, decode_times=False) as xrdf:
		for k in xrdf.keys():
			try:
				print "First Data Point: {key} - {value}".format(key=k, value=xrdf[k].values[0,0,0,0])
				if (xrdf[k].values[:,0,0,0] == 1e35).all():
					print "All Data points are 1e35"
			except IndexError:
				print "First Data Point: {key} - {value}".format(key=k, value=xrdf[k].values[0])
				if (xrdf[k].values[:] == 1e35).all():
					print "All Data points are 1e35"				

if args.indir:
	for infile in os.listdir(args.indir):
		try:
			with xr.open_dataset(args.indir + infile, decode_times=False) as xrdf:
				print "\n Checking {file}".format(file=args.indir + infile)
				for k in xrdf.keys():
					try:
						print "First Data Point: {key} - {value}".format(key=k, value=xrdf[k].values[0,0,0,0])
						if (xrdf[k].values[:,0,0,0] == 1e35).all():
							print "All Data points are 1e35"
					except IndexError:
						print "First Data Point: {key} - {value}".format(key=k, value=xrdf[k].values[0])
						if (xrdf[k].values[:] == 1e35).all():
							print "All Data points are 1e35"
		except:
			pass