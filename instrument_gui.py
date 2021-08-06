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

# basic test

class Instrument_gui(object):

    def __init__(self, **kwargs):

        self.instrument = None
        self.gui_widgets = {}
        self.parameters = None
        self.layout = w.Layout(display='flex',
                    flex_flow='line',
            width='100%'
        )

    def set_instrument(self, instrument):
        self.instrument = instrument

    def get_parameters(self):
        if self.instrument is not None:
            self.parameters = self.instrument.parameters

    def make_get_button(self, p_name):
        # param is a string, parameter name
        self.gui_widgets['%s get_button' % p_name] = w.Button(description='Get')
        self.gui_widgets['%s get_out' % p_name] = w.Output()
        def on_button_clicked(b):
            try:
                with self.gui_widgets['%s get_out' % p_name]:
                    self.gui_widgets['%s selector' % p_name].value = \
                        self.instrument.get(p_name)
            finally:
                time.sleep(0.5)
        self.gui_widgets['%s get_callback' % p_name] = on_button_clicked
        self.gui_widgets['%s get_button' % p_name].on_click(self.gui_widgets['%s get_callback' % p_name])

    def make_set_button(self, p_name):
        # param is a string, parameter name
        self.gui_widgets['%s set_button' % p_name] = w.Button(description='Set')
        self.gui_widgets['%s set_out' % p_name] = w.Output()
        def on_button_clicked(b):
            # self.lock.acquire()
            try:
                with self.gui_widgets['%s set_out' % p_name]:
                    self.instrument.set(p_name, self.gui_widgets['%s selector' % p_name].value)
            finally:
                # self.lock.release()
                time.sleep(0.5)
        self.gui_widgets['%s set_callback' % p_name] = on_button_clicked
                # linking button and function together using a button's method
        self.gui_widgets['%s set_button' % p_name].on_click(self.gui_widgets['%s set_callback' % p_name])

    def make_get_all_button(self):
        self.gui_widgets['get_all_button'] = w.Button(description='Get all')
        self.gui_widgets['get_all_out'] = w.Output()
        def on_button_clicked(b):
            try:
                with self.gui_widgets['get_all_out']:
                    for p in self.parameters:
                        try:
                            self.gui_widgets['%s selector' % p].value = self.instrument.get(p)
                            self.logger.info('parameter %s gotten' % p)
                        except:
                            pass
            finally:
                time.sleep(0.5)
        self.gui_widgets['get_all_callback'] = on_button_clicked
        self.gui_widgets['get_all_button'].on_click(self.gui_widgets['get_all_callback'])

    def create_gui(self):
        style = {'description_width':'initial'}
        vline = []
        for p in self.parameters:
            hline = []
            if 'value' not in self.parameters[p] and \
                self.parameters[p]['flags']['get']:
                self.instrument.get(p)
            if self.parameters[p]['type'] is float:
                self.gui_widgets['%s selector' % p] = w.FloatSlider(
                    value=self.parameters[p]['value'],
                    min=self.parameters[p]['range'][0],
                    max=self.parameters[p]['range'][1],
                    step=self.parameters[p]['step'],
                    description=self.parameters[p]['description'], style=style)
            if self.parameters[p]['type'] is int:
                self.gui_widgets['%s selector' % p] = w.IntSlider(
                    value=self.parameters[p]['value'],
                    min=self.parameters[p]['range'][0],
                    max=self.parameters[p]['range'][1],
                    description=self.parameters[p]['description'], style=style)    
            if self.parameters[p]['type'] is bool:
                self.gui_widgets['%s selector' % p] = w.Dropdown(
                    options=['True', 'False'],
                    description=self.parameters[p]['name'], style=style)
            hline.append(self.gui_widgets['%s selector' % p])
            if self.parameters[p]['flags']['get']:
                self.make_get_button(p)
                hline.append(self.gui_widgets['%s get_button' % p])
            if self.parameters[p]['flags']['set']:
                self.make_set_button(p)
                hline.append(self.gui_widgets['%s set_button' % p])
            vline.append(w.HBox(hline))
        self.make_get_all_button()
        vline.append(w.HBox([self.gui_widgets['get_all_button']]))
        self.gui = w.VBox(vline)
        display(self.gui)