# This file contains standard including file for the objreader
import os
import sys
import getpass

if ( getpass.getuser() == 'ksuvee' or getpass.getuser() == 'TofuYui' ):

    TOP_DIR = os.path.dirname( os.path.dirname(__file__) )

    sys.path.insert( 0, TOP_DIR + r'\objreader' )
    sys.path.insert( 1, TOP_DIR + r'\julich' )
    sys.path.insert( 2, TOP_DIR + r'\density' )

elif ( getpass.getuser() == 'seanc' or getpass.getuser() == 'Sean'):
    sys.path.insert( 0, r'\projects\crowd\fund_diag\paper\pre_density\experiment' )
    sys.path.insert( 0, r'\projects\objreader' )
    sys.path.insert( 0, r'\projects\seyfried\density' )

