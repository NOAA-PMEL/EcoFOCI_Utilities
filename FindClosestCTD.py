#!/usr/bin/env python

"""
 FindClosestCTD.py
 
 Using the Cruise log database, search for CTD's within a specified range of a location


 History
 =======
 2019-07-15: Make python3 compliant: WIP

 Future
 ======

 Compatibility:
 ==============
 python >=3.6 **Tested
 python 2.7 Tested but not developed for and may break

 """

# System Stack
import datetime
import argparse
import sys

# Science Stack
import mysql.connector

# User defined
import io_utils.ConfigParserLocal as ConfigParserLocal
import calc.haversine as sphered

__author__ = "Shaun Bell"
__email__ = "shaun.bell@noaa.gov"
__created__ = datetime.datetime(2016, 9, 28)
__modified__ = datetime.datetime(2016, 9, 28)
__version__ = "0.1.0"
__status__ = "Development"


"""--------------------------------SQL Init----------------------------------------"""


class NumpyMySQLConverter(mysql.connector.conversion.MySQLConverter):
    """ A mysql.connector Converter that handles Numpy types """

    def _float32_to_mysql(self, value):
        if np.isnan(value):
            return None
        return float(value)

    def _float64_to_mysql(self, value):
        if np.isnan(value):
            return None
        return float(value)

    def _int32_to_mysql(self, value):
        if np.isnan(value):
            return None
        return int(value)

    def _int64_to_mysql(self, value):
        if np.isnan(value):
            return None
        return int(value)


def connect_to_DB(**kwargs):
    # Open database connection
    try:
        db = mysql.connector.connect(use_pure=True, **kwargs)
    except mysql.connector.Error as err:
        """
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
      else:
        print(err)
      """
        print("error - will robinson")

    db.set_converter_class(NumpyMySQLConverter)

    # prepare a cursor object using cursor() method
    cursor = db.cursor(dictionary=True)
    prepcursor = db.cursor(prepared=True)
    return (db, cursor)


def close_DB(db):
    # disconnect from server
    db.close()


def read_data(db, cursor, table, yearrange):

    """

    """
    sql = (
        "SELECT `id`,`LatitudeDeg`,`LatitudeMin`,`LongitudeDeg`,"
        "`LongitudeMin`,`ConsecutiveCastNo`,`UniqueCruiseID`,`GMTDay`,"
        "`GMTMonth`,`GMTYear`,`MaxDepth` from `{table}` WHERE `GMTYear` BETWEEN '{startyear}' AND '{endyear}'"
    ).format(table=table, startyear=yearrange[0], endyear=yearrange[1])
    print(sql)

    result_dic = {}
    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Get column names
        rowid = {}
        counter = 0
        for i in cursor.description:
            rowid[i[0]] = counter
            counter = counter + 1
        # print rowid
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            result_dic[row["UniqueCruiseID"] + "_" + row["ConsecutiveCastNo"]] = {
                keys: row[keys] for val, keys in enumerate(row.keys())
            }
        return result_dic
    except:
        print("Error: unable to fecth data")


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
            counter = counter + 1
        # print rowid
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            result_dic[row["MooringID"]] = {
                keys: row[keys] for val, keys in enumerate(row.keys())
            }
        return result_dic
    except:
        print("Error: unable to fecth data")


"""------------------------------------------------------------------------------------"""
parser = argparse.ArgumentParser(
    description="Find Closest CTD casts to Mooring Deployment"
)

parser.add_argument(
    "DistanceThreshold",
    metavar="DistanceThreshold",
    type=float,
    help="Distance From Mooring in Kilometers",
)
parser.add_argument(
    "YearRange",
    metavar="YearRange",
    type=int,
    nargs=2,
    help="Range of years to look (eg 2012 2014)",
)
parser.add_argument(
    "-db_moor",
    "--db_moorings",
    type=str,
    help="path to db .pyini file for mooring records",
)
parser.add_argument(
    "-db_ctd", "--db_ctd", type=str, help="path to db .pyini file for ctd records"
)
parser.add_argument(
    "-MooringID", metavar="--MooringID", type=str, help="MooringID 13BSM-2A"
)
parser.add_argument(
    "-latlon",
    "--latlon",
    nargs="+",
    type=float,
    help="use manual lat/lon (decimaldegrees +N,+W)",
)

args = parser.parse_args()

host = "akutan"

if not args.latlon and not args.MooringID:
    print("Choose either a mooring location or a lat/lon pairing")
    sys.exit()

if args.latlon:  # manual input of lat/lon
    location = [args.latlon[0], args.latlon[1]]

if args.MooringID:
    # get information from local config file - a json/yaml formatted file
    if args.db_moorings:
        db_config = ConfigParserLocal.get_config(args.db_moorings)
    else:
        db_config = ConfigParserLocal.get_config(
            "../EcoFOCI_Config/AtSeaPrograms/db_config_mooring.yaml", "yaml"
        )

    print(db_config)
    # get db meta information for mooring
    ### connect to DB
    (db, cursor) = connect_to_DB(
        host=db_config["systems"][host]["host"],
        user=db_config["login"]["user"],
        password=db_config["login"]["password"],
        database=db_config["database"]["database"],
        port=db_config["systems"][host]["port"],
    )
    table = "mooringdeploymentlogs"
    Mooring_Meta = read_mooring(db, cursor, table, args.MooringID)
    close_DB(db)

    # location = [71 + 13.413/60., 164 + 14.98/60.]
    location = [
        float(Mooring_Meta[args.MooringID]["Latitude"].split()[0])
        + float(Mooring_Meta[args.MooringID]["Latitude"].split()[1]) / 60.0,
        float(Mooring_Meta[args.MooringID]["Longitude"].split()[0])
        + float(Mooring_Meta[args.MooringID]["Longitude"].split()[1]) / 60.0,
    ]


threshold = args.DistanceThreshold  # km

# get information from local config file - a json/yaml formatted file
if args.db_ctd:
    db_config = ConfigParserLocal.get_config(args.db_moorings)
else:
    db_config = ConfigParserLocal.get_config(
        "../EcoFOCI_Config/AtSeaPrograms/db_config_cruises.yaml", "yaml"
    )

# get db meta information for mooring
### connect to DB
(db, cursor) = connect_to_DB(
    host=db_config["systems"][host]["host"],
    user=db_config["login"]["user"],
    password=db_config["login"]["password"],
    database=db_config["database"]["database"],
    port=db_config["systems"][host]["port"],
)
table = "cruisecastlogs"
cruise_data = read_data(db, cursor, table, args.YearRange)
db.close()

for index in sorted(cruise_data.keys()):

    destination = [
        cruise_data[index]["LatitudeDeg"] + cruise_data[index]["LatitudeMin"] / 60.0,
        cruise_data[index]["LongitudeDeg"] + cruise_data[index]["LongitudeMin"] / 60.0,
    ]
    Distance2Station = sphered.distance(location, destination)

    if Distance2Station <= threshold:
        print(
            "Cast {0} on Cruise {1} is {2:3.2f} km away - {3}-{4}-{5} and {6}m deep".format(
                cruise_data[index]["ConsecutiveCastNo"],
                cruise_data[index]["UniqueCruiseID"],
                Distance2Station,
                cruise_data[index]["GMTYear"],
                cruise_data[index]["GMTMonth"],
                cruise_data[index]["GMTDay"],
                cruise_data[index]["MaxDepth"],
            )
        )
