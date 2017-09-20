#!/usr/bin/env python

"""
Background
----------

 mag_declination_correction.py
 
 Purpose:
 --------
 Calculate the magnetic declination correction for either a known EcoFOCI mooring in the 
 existing database, or for a defined latitude/longitude pair

 History:
 --------
 
 2016-10-21: Move routine to EcoFOCI_utilities to unify program calls


"""

# Standard library.
import datetime

# System Stack
import argparse
import pymysql


# User Stack
import calc.geomag.geomag.geomag as geomag
from io_utils.EcoFOCI_db_io import EcoFOCI_db_mooring

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2014, 01, 13)
__modified__ = datetime.datetime(2014, 01, 29)
__version__  = "0.2.0"
__status__   = "Development"

"""--------------------------------lat/lon----------------------------------------"""
       
def latlon_convert(Mooring_Lat, Mooring_Lon):
    
    tlat = Mooring_Lat.strip().split() #deg min dir
    lat = float(tlat[0]) + float(tlat[1]) / 60.
    if tlat[2] == 'S':
        lat = -1 * lat
        
    tlon = Mooring_Lon.strip().split() #deg min dir
    lon = float(tlon[0]) + float(tlon[1]) / 60.
    if tlon[2] == 'E':
        lon = -1 * lon
        
    return (lat, lon)

"""------------------------------- MAIN ----------------------------------------"""

parser = argparse.ArgumentParser(description='Magnetic Declination Correction')
parser.add_argument('-mid', '--MooringID', type=str,
               help='MooringID 13BSM-2A')       
parser.add_argument('-latlon', '--latlon', type=float, nargs='+',
               help='correction for now using \
               decimal degree lat/lon pair seperated by a space eg 52.5 -170.25')                 
parser.add_argument('-dt','--datetime', type=str,
               help='use this flag to add a user specified date of form \
               yyyy-mm-dd')

args = parser.parse_args()


if args.MooringID:
    #get information from local config file - a json formatted file
    EcoFOCI_db = EcoFOCI_db_mooring()
    config_file = '/Volumes/WDC_internal/Users/bell/Programs/Python/db_connection_config_files/db_config_mooring.pyini'
    (db,cursor) = EcoFOCI_db.connect_to_DB(db_config_file=config_file)

    Mooring_Meta = EcoFOCI_db.read_mooring_summary(table='mooringdeploymentlogs', 
                                           mooringid=args.MooringID)
    EcoFOCI_db.close()


    Mooring_Lat = Mooring_Meta[args.MooringID]['Latitude']
    Mooring_Lon = Mooring_Meta[args.MooringID]['Longitude']  

    dep_date = Mooring_Meta[args.MooringID]['DeploymentDateTimeGMT'].date()

    (lat,lon) = latlon_convert(Mooring_Lat, Mooring_Lon)

    t = geomag.GeoMag()
    dec = t.GeoMag(lat,-1 * lon,time=dep_date).dec

    print ("At Mooring {0}, with lat: {1} (N) , lon: {2} (W) the declination correction is {3}").format(args.MooringID, lat, lon, dec)

if args.latlon:

    lat = args.latlon[0]
    lon = args.latlon[1]
    if args.datetime:
        dep_date=datetime.datetime.strptime(args.datetime,'%Y-%m-%d').date()
    else:
        dep_date=datetime.datetime.now().date()

    t = geomag.GeoMag()
    dec = t.GeoMag(lat,-1 * lon,time=dep_date).dec

    print ("At Mooring {0}, with lat: {1} (N) , lon: {2} (W) the declination correction is {3}").format(args.MooringID, lat, lon, dec)
