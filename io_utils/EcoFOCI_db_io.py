#!/usr/bin/env python

"""
 Background:
 --------
 EcoFOCI_db_io.py
 
 
 Purpose:
 --------
 Various Routines and Classes to interface with the mysql database that houses EcoFOCI meta data
 
 History:
 --------

 2019-08-07: SW Bell - make python3 compliant

"""

import mysql.connector
import ConfigParserLocal 
import datetime

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2014, 1, 29)
__modified__ = datetime.datetime(2016, 8, 10)
__version__  = "0.1.0"
__status__   = "Development"
__keywords__ = 'netCDF','meta','header'

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

class EcoFOCI_db_mooring(object):
    """Class definitions to access EcoFOCI Mooring Database"""

    def connect_to_DB(self, db_config_file=None):
        """Try to establish database connection

        Parameters
        ----------
        db_config_file : str
            full path to json formatted database config file    

        """
        self.db_config = ConfigParserLocal.get_config(db_config_file)
        try:
            self.db = mysql.connector.connect(self.db_config['host'], 
                                      self.db_config['user'],
                                      self.db_config['password'], 
                                      self.db_config['database'], 
                                      self.db_config['port'])
        except:
            print "db error"
            
        # prepare a cursor object using cursor() method
        self.cursor = self.db.cursor(mysql.connector.cursors.DictCursor)
        return(self.db,self.cursor)

    def manual_connect_to_DB(self, host='localhost', user='viewer', 
                             password=None, database='ecofoci', port=3306):
        """Try to establish database connection

        Parameters
        ----------
        host : str
            ip or domain name of host
        user : str
            account user
        password : str
            account password
        database : str
            database name to connect to
        port : int
            database port

        """
        db_config = {}     
        db_config['host'] = host
        db_config['user'] = user
        db_config['password'] = password
        db_config['database'] = database
        db_config['port'] = port

        try:
            self.db = mysql.connector.connect(**db_config)
        except:
            print("db error")
            
        # prepare a cursor object using cursor() method
        self.cursor = self.db.cursor(dictionary=True)
        self.prepcursor = self.db.cursor(prepared=True)
        return(self.db,self.cursor)


    def read_mooring_summary(self, table=None, verbose=False, **kwargs):
        """ output is mooringID indexed """
        if 'mooringid' in kwargs.keys():
            sql = ("SELECT * FROM `{0}` WHERE `MooringID`='{1}'").format(table, kwargs['mooringid'])
        else:
            sql = ("SELECT * FROM `{0}` ").format(table)

        if verbose:
            print(sql)

        if verbose:
            print(sql)

        result_dic = {}
        try:
            self.cursor.execute(sql)
            for row in self.cursor:
                result_dic[row['MooringID']] ={keys: row[keys] for val, keys in enumerate(row.keys())} 
            return (result_dic)
        except:
            print("Error: unable to fetch data")


    def close(self):
        """close database"""
        self.prepcursor.close()
        self.cursor.close()
        self.db.close()

