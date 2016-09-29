#!/usr/bin/env python

"""
 FindClosestCTD.py
 
 Using the Cruise log database, search for CTD's within a specified range of a location

 Using Anaconda packaged Python 
"""

#System Stack
import datetime
import argparse

#Science Stack
import pymysql

# User defined
import utilities.ConfigParserLocal as ConfigParserLocal
import utilities.haversine as sphered

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2014, 06, 13)
__modified__ = datetime.datetime(2014, 06, 13)
__version__  = "0.1.0"
__status__   = "Development"

    
"""--------------------------------SQL Init----------------------------------------"""
def connect_to_DB(host, user, password, database, port=3306):
    # Open database connection
    try:
        db = pymysql.connect(host, user, password, database, port)
    except:
        print "db error"
        
    # prepare a cursor object using cursor() method
    cursor = db.cursor(pymysql.cursors.DictCursor)
    return(db,cursor)
    


def read_data(db, cursor, table, startyear):

    
    """Hardcoded database has following parameters:
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `Vessel` varchar(30) DEFAULT NULL COMMENT 'Full Name (e.g.Dyson)',
    `CruiseID` varchar(12) NOT NULL DEFAULT '' COMMENT 'ssYY## (where s is ship, Y is year, # is sequential cruise number)',
    `Project_Leg` enum('','L1','L2','L3','L4') DEFAULT '' COMMENT 'L2/L2',
    `UniqueCruiseID` varchar(22) DEFAULT NULL COMMENT 'CruiseID + Leg',
    `Project` text COMMENT 'project name',
    `StationNo_altname` text,
    `ConsecutiveCastNo` varchar(6) NOT NULL DEFAULT '' COMMENT 'CTD001',
    `LatitudeDeg` int(4) NOT NULL COMMENT '(+/N , -/S)',
    `LatitudeMin` float NOT NULL COMMENT 'decimal seconds',
    `LongitudeDeg` int(3) NOT NULL COMMENT '(+/W, -/E)',
    `LongitudeMin` float NOT NULL COMMENT 'decimal seconds',
    `GMTDay` int(2) NOT NULL COMMENT '0-31',
    `GMTMonth` varchar(3) NOT NULL DEFAULT '' COMMENT 'mmm',
    `GMTYear` int(4) NOT NULL COMMENT 'yyyy',
    `GMTTime` time NOT NULL DEFAULT '00:00:00' COMMENT 'hh:mm:ss',
    ,

    """
    sql = "SELECT `id`,`LatitudeDeg`,`LatitudeMin`,`LongitudeDeg`,`LongitudeMin`,`ConsecutiveCastNo`,`UniqueCruiseID`,`GMTDay`,`GMTMonth`,`GMTYear` from `%s` WHERE `GMTYear` >= '%s'" % (table, startyear)
    print sql
    
    result_dic = {}
    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Get column names
        rowid = {}
        counter = 0
        for i in cursor.description:
            rowid[i[0]] = counter
            counter = counter +1 
        #print rowid
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            result_dic[row['id']] ={keys: row[keys] for val, keys in enumerate(row.keys())} 
        return (result_dic)
    except:
        print "Error: unable to fecth data"

def read_mooring(db, cursor, table, MooringID):
    sql = ("SELECT * from `{0}` WHERE `MooringID`= '{1}' ").format(table, MooringID)
    
    result_dic = {}
    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Get column names
        rowid = {}
        counter = 0
        for i in cursor.description:
            rowid[i[0]] = counter
            counter = counter +1 
        #print rowid
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            result_dic[row['MooringID']] ={keys: row[keys] for val, keys in enumerate(row.keys())} 
        return (result_dic)
    except:
        print "Error: unable to fecth data"

"""------------------------------------------------------------------------------------"""
parser = argparse.ArgumentParser(description='Find Closest CTD casts to Mooring Deployment')
parser.add_argument('MooringID', metavar='MooringID', type=str,
               help='MooringID 13BSM-2A')               
parser.add_argument('DistanceThreshold', metavar='DistanceThreshold', type=float,
               help='Distance From Mooring in Kilometers')
parser.add_argument('StartYear', metavar='StartYear', type=int,
               help='Earliest Year to start looking')
parser.add_argument('-db_moor', '--db_moorings', type=str, help='path to db .pyini file for mooring records')               
parser.add_argument('-db_ctd', '--db_ctd', type=str, help='path to db .pyini file for ctd records')               
               
args = parser.parse_args()

#get information from local config file - a json formatted file
if args.db_moorings:
    db_config = ConfigParserLocal.get_config(args.db_moorings)
else:
    db_config = ConfigParserLocal.get_config('../../db_connection_config_files/db_config_mooring.pyini')

#get db meta information for mooring
### connect to DB
(db,cursor) = connect_to_DB(db_config['host'], db_config['user'], db_config['password'], db_config['database'], db_config['port'])
table = 'mooringdeploymentlogs'
Mooring_Meta = read_mooring(db, cursor, table, args.MooringID)
db.close()

#location = [71 + 13.413/60., 164 + 14.98/60.]
location = [float(Mooring_Meta[args.MooringID]['Latitude'].split()[0]) + float(Mooring_Meta[args.MooringID]['Latitude'].split()[1])/60.,
            float(Mooring_Meta[args.MooringID]['Longitude'].split()[0]) + float(Mooring_Meta[args.MooringID]['Longitude'].split()[1])/60.]

threshold = args.DistanceThreshold #km

#get information from local config file - a json formatted file
if args.db_ctd:
    db_config = ConfigParserLocal.get_config(args.db_moorings)
else:
    db_config = ConfigParserLocal.get_config('../../db_connection_config_files/db_config_cruises.pyini')

#get db meta information for mooring
### connect to DB
(db,cursor) = connect_to_DB(db_config['host'], db_config['user'], db_config['password'], db_config['database'], db_config['port'])
table = 'cruisecastlogs'
cruise_data = read_data(db, cursor, table, args.StartYear)
db.close()

for index in cruise_data.keys():

    destination = [cruise_data[index]['LatitudeDeg']+cruise_data[index]['LatitudeMin']/60.,\
                    cruise_data[index]['LongitudeDeg']+cruise_data[index]['LongitudeMin']/60.]    
    Distance2Station = sphered.distance(location,destination)

    if Distance2Station <= threshold:
        print ("Cast {0} on Cruise {1} is {2} km away - {3}-{4}-{5}").format(cruise_data[index]['ConsecutiveCastNo'],\
                cruise_data[index]['UniqueCruiseID'],Distance2Station,cruise_data[index]['GMTYear'],\
                cruise_data[index]['GMTMonth'],cruise_data[index]['GMTDay'])
