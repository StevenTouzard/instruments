import sys
import pyvisa
import time #Required to use delay functions
import ipywidgets as w
from IPython.display import display
from threading import Thread, Lock
# import threading
import logging
import matplotlib.pyplot as plt
import json
import os
import glob
import csv
import numpy as np
from instrument import Instrument, VisaInstrument


class rigol_DG832(VisaInstrument):

    def __init__(self, name, **kwargs):
        super(rigol_DG832, self).__init__(name, **kwargs)

        for i in [1, 2]:
            self.add_visa_parameter('frequency_ch_'+str(i),
                'SOUR%i:FREQ?' % i, 'SOUR%i:FREQ ' % i, type=float, range=[0, 35e6],
                step=0.1)
            self.add_visa_parameter('phase_ch_'+str(i),
                'SOUR%i:PHAS?' % i, 'SOUR%i:PHAS ' % i, type=float, range=[0, 360],
                step=0.01)
        