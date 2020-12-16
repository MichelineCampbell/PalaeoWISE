#!/usr/bin/env python
# -*- coding: utf-8 -*-
#==============================================================================
# Extra LiPD routines:
#
#   Read_JSON         - Read metadata and return JSON structure
#   Read_CSV2DF       - Read internal CSV file and return dataframe
#   print_nested_dict - Print LiPD structure to screen
#   write_nested_dict - Write LiPD structure to file
#   extract_values    - Extract data from complex JSON
#   extract_string1   - Extract first "data item from complex JSON" as string
#
#------------------------------------------------------------------------------
# Notes:
#
#------------------------------------------------------------------------------
# By John Vitkovsky
# Modified 01-09-2020
# Queensland Hydrology, Queensland Government
#
#==============================================================================


# Modules:
import sys, os
import numpy as np
import pandas as pd
from zipfile import ZipFile
import json


# Variables:
DEBUG = 0  # 0=None, 1=Some, 2=More




#------------------------------------------------------------------------------
# Read metadata and return JSON structure
#------------------------------------------------------------------------------
def Read_JSON(lipd_file):
    zf = ZipFile(lipd_file)
    with zf.open('bag/data/metadata.jsonld') as f:  
        # jf = json.loads(f.read())
        jf = json.loads(f.read().decode('cp1252'))
        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0x96 in position 1923: invalid start byte
        # fr = f.read()
        # fr = fr.replace(b'\x96', b'\x2D')  # En dash
        # fr = fr.replace(b'\x92', b'\x27')  # Right single quote
        # fr = fr.decode('utf-8', 'replace')  # Last resort
        # jf = json.loads(fr)
    return jf
# end def




#------------------------------------------------------------------------------
# Read internal CSV file and return dataframe
#------------------------------------------------------------------------------
def Read_CSV2DF(lipd_file, csv_file):
    zf = ZipFile(lipd_file)
    # df = pd.read_csv(zf.open('bag/data/' + csv_file))
    # There are no column names in LiPD CSVs.
    df = pd.read_csv(zf.open('bag/data/' + csv_file), header=None)
    return df
# end def




#------------------------------------------------------------------------------
# Print LiPD structure to screen
#   - Only for nested dictionaries.
#   - Will include dictionaries+lists in the future.
#------------------------------------------------------------------------------
def print_nested_dict(d, indent=0):
    for key, value in d.items():
        print('')
        print(indent * ' '  + str(key), end=':')
        if isinstance(value, dict):
            print_nested_dict(value, indent + 2)
        else:
            s = str(value)
            if len(s) < 40:
                print(' ' + s, end='')
            else:
                print(' ' + s[:40] + '...', end='')
        # end if
    # end for
# end def

 


#------------------------------------------------------------------------------
# Write LiPD structure to file
#   - Only for nested dictionaries.
#   - Will include dictionaries+lists in the future.
#------------------------------------------------------------------------------
def write_nested_dict(file, data):

    def write_nested_dict_helper(f, d, indent=0):
        for key, value in d.items():
            f.write(indent * ' '  + str(key) + ':')
            if isinstance(value, dict):
                f.write('\n')
                write_nested_dict_helper(f, value, indent + 2)
            else:
                s = str(value)
                if len(s) < 40:
                    f.write(' ' + s + '\n')
                else:
                    f.write(' ' + s[:40] + '...' + '\n')
            # end if
        # end for
    # end def

    with open(file, 'w') as f:
        write_nested_dict_helper(f, data)
    # end with

# end def




#------------------------------------------------------------------------------
# Extract data from complex JSON
#   https://hackersandslackers.com/extract-data-from-complex-json-python/
#   Modified to do case-insensitive search
#------------------------------------------------------------------------------
def extract_values(obj, key, case = True):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif case:
                    if k == key: arr.append(v)
                else:
                    if k.upper() == key.upper(): arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results
# end def




#------------------------------------------------------------------------------
# Extract first "data item from complex JSON" as string
#   - Optional case-sensitive search flag
#   - Optional return value if missing
#------------------------------------------------------------------------------
def extract_string1(obj, key, case = True, missing = ''):
    arr = extract_values(obj, key, case)
    if len(arr) == 0:
        return missing
    else:
        return str(arr[0])
    # end if
# end def

