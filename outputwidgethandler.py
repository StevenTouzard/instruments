import sys
import pyvisa
import time #Required to use delay functions
import ipywidgets as w
from IPython.display import display
from threading import Thread, Lock
import threading
import logging
import matplotlib.pyplot as plt
import json
import os
import glob
import csv
import numpy as np
import instrument

class OutputWidgetHandler(logging.FileHandler):
    """ Custom logging handler sending logs to an output widget """

    def __init__(self, filename, *args, **kwargs):
        super(OutputWidgetHandler, self).__init__(filename, *args, **kwargs)
        layout = {
            'width': '100%',
            'height': '160px',
            'border': '1px solid black'
        }
        self.out = w.Output(layout=layout)

    def emit(self, record):
        """ Overload of logging.Handler method """
        formatted_record = self.format(record)
        new_output = {
            'name': 'stdout',
            'output_type': 'stream',
            'text': formatted_record+'\n'
        }
        self.out.outputs = (new_output, ) + self.out.outputs

    def show_logs(self):
        """ Show the logs """
        display(self.out)

    def clear_logs(self):
        """ Clear the current logs """
        self.out.clear_output()