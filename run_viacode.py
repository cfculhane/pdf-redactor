# -*- coding: utf-8 -*-
"""
@author: hibellm

1. TO RUN THE REDACTION CODE WITHIN PYTHON

INPUTS:   ANON - FOR FULL ANONYMIZATION OF THE TABLE
          RCR  - FOR DOUBLE-CODING OF THE TABLE

"""

import os
import subprocess
import re
from datetime import datetime

import pdf_redactor


# WORK OUT THE PATHS TO THE FILES
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_PATH ='.'


def run_eg(fin, fout):

    command1 = '/home/bceuser/hibellm/.conda/envs/anon/bin/python example.py <'+fin+'>'+fout;
    try:
        #subprocess.run(os.path.join(APP_ROOT, APP_PATH, 'function', command1), shell=True, check=True)
        subprocess.run(command1, shell=True, check=True)
        print('Updated meta data RWD_META_MDH.VendorDetails', 'green')
    except:
        print('ERROR: The code did not run RWD_META_MDH.VendorDetails', 'red')

run_eg('test-ssns.pdf','test_python2.pdf')
