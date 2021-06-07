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
import types
import copy

class Instrument:

    def __init__(self, name, logger=None, **kwargs):

        self.name = name
        self.parameters = {}
        self.addr = None
        self.model = None
        self.logger = logger
        self._added_methods = []
        self.driver = None

    # def add_parameter(self, p_name, p_type, p_value, p_range=None, 
    #     p_get=True, p_set=True, p_step=None):
    #         self.parameters[p_name] = {}
    #         self.parameters[p_name]['value'] = p_value
    #         self.parameters[p_name]['name'] = p_name
    #         self.parameters[p_name]['type'] = p_type
    #         self.parameters[p_name]['get'] = p_get 
    #         self.parameters[p_name]['set'] = p_set
    #         self.parameters[p_name]['range'] = p_range
    #         self.parameters[p_name]['step'] = p_step
    #         if self.parameters[p_name]['range'] is None and \
    #             self.parameters[p_name]['type'] == 'float': 
    #             self.parameters[p_name]['range'] = (0.,
    #             2*self.parameters[p_name]['value']) 
    #             #careful the range could be 0 to 0
    #         if self.parameters[p_name]['range'] is None and \
    #             self.parameters[p_name]['type'] == 'float': 
    #             self.parameters[p_name]['step'] = (
    #             self.parameters[p_name]['range'][1] - \
    #             self.parameters[p_name]['range'][0]) / 1000.0
    #         if self.parameters[p_name]['type'] == 'int' and \
    #             self.parameters[p_name]['range'] is None:
    #             self.parameters[p_name]['range'] = (0, 1)

    def get_parameter_options(self, name):
        '''
        Return list of options for paramter.

        Input: name (string)
        Output: dictionary of options
        '''
        if name in self.parameters:
            return self.parameters[name]
        else:
            return None

    def add_parameter(self, name, **kwargs):
        '''
        Create an instrument 'parameter' that is known by the whole
        environment (gui etc).

        This function creates the 'get_<name>' and 'set_<name>' wrapper
        functions that will perform checks on parameters and finally call
        '_do_get_<name>' and '_do_set_<name>'. The latter functions should
        be implemented in the instrument driver.

        Input:
            name (string): the name of the parameter (string)
            optional keywords:
                type: types.FloatType, types.StringType, etc.
                flags: bitwise or of Instrument.FLAG_ constants.
                    If not set, FLAG_GETSET is default
                channels: tuple. Automagically create channels, e.g.
                    (1, 4) will make channels 1, 2, 3, 4.
                minval, maxval: values for bound checking
                units (string): units for this parameter
                maxstep (float): maximum step size when changing parameter
                stepdelay (float): delay when setting steps (in milliseconds)
                tags (array): tags for this parameter
                doc (string): documentation string to add to get/set functions
                format_map (dict): map describing allowed options and the
                    formatted (mostly GUI) representation
                option_list (array/tuple): allowed options
                persist (bool): if true load/save values in config file
                probe_interval (int): interval in ms between automatic gets
                listen_to (list of (ins, param) tuples): list of parameters
                    to watch. If any of them changes, execute a get for this
                    parameter. Useful for a parameter that depends on one
                    (or more) other parameters.

        Output: None
        '''
        if name in self.parameters:
            self.logger.error('Parameter %s already exists.', name)
            return

        options = kwargs

        if 'flags' not in options:
            options['flags'] = {}
            options['flags']['get'] = True 
            options['flags']['set'] = True
        if 'type' not in options:
            options['type'] = None
        if 'tags' not in options:
            options['tags'] = []
        if 'description' not in options:
            options['description'] = name

        # If defining channels call add_parameter for each channel
        if 'channels' in options:
            if len(options['channels']) == 2 and type(options['channels'][0]) is int:
                minch, maxch = options['channels']
                channels = range(minch, maxch + 1)
            else:
                channels = options['channels']

            for i in channels:
                chopt = copy.copy(options)
                del chopt['channels']
                chopt['channel'] = i
                chopt['base_name'] = name

                if 'channel_prefix' in options:
                    var_name = options['channel_prefix'] % i + name
                else:
                    var_name = '%s%s' % (name, i)

                self.add_parameter(var_name, **chopt)

        if 'channel' in options:
            ch = options['channel']
        else:
            ch = None
            return

        self.parameters[name] = options

        if options['flags']['get']:
            if ch is not None:
                func = lambda query=True, **lopts: \
                    self.get(name, query=query, channel=ch, **lopts)
            else:
                func = lambda query=True, **lopts: \
                    self.get(name, query=query, **lopts)

            setattr(self, 'get_%s' % name,  func)
            self._added_methods.append('get_%s' % name)  

        if options['flags']['set']:
            if ch is not None:
                func = lambda val, **lopts: self.set(name, val, channel=ch, **lopts)
            else:
                func = lambda val, **lopts: self.set(name, val, **lopts)

            setattr(self, 'set_%s' % name, func)
            self._added_methods.append('set_%s' % name)

        # if 'value' not in self.parameters[name] and \
        #     self.parameters[name]['flags']['get']:
        #     self.get(name, **kwargs)


    def get(self, name, query=True, **kwargs):
        self.logger.info('I got '+ name)
        try:
            p = self.parameters[name]
        except:
            self.logger.error('Could not retrieve options for parameter %s' % name)
            return None
        if self.driver == 'visa':
            kwargs['channel'] = name
        if not query:
            if 'value' in p:
                return p['value']
            else:
                self.logger.error('Parameter has no value')
                return None
        else:
            func = p['get_func']
            value = func(**kwargs)

        p['value'] = value
        return value

    def set(self, name, value, **kwargs):

        self.logger.info('I am setting %s' % name)
        if self.driver == 'visa':
            kwargs['channel'] = name
        try:
            p = self.parameters[name]
        except:
            self.logger.error('Could not retrieve options for parameter %s' % name)
        
        func = p['set_func']
        ret = func(value, **kwargs)

        p['value'] = value
        return value


    # def save_parameters(self):
    #     try:
    #         os.makedirs(settings_path)
    #     except FileExistsError:
    #         pass
    #     ts = time.strftime('%Y%m%d%H%M%S', time.gmtime())
    #     with open(r'%s\%s_%s.txt' % (settings_path, ts, self.name), 'w') as json_file:
    #         json.dump(self.parameters, json_file)


class VisaInstrument(Instrument):
    def __init__(self, name, **kwargs):

        self.ins = None

        super(VisaInstrument, self).__init__(name, **kwargs)

    def create_visa_instrument(self, rm, model, addr):
        self.ins = rm.open_resource(addr)
        self.addr = addr 
        self.model = model
        self.driver = 'visa'

    def check_ins(self):
        if self.ins is None:
            raise Exception('instrument not open')

    def write(self, cmd):
        self.check_ins()
        self.ins.write(cmd)

    def ask(self, cmd, timeout=None):
        self.write(cmd)
        return self.ins.read()

    def get_visa_param(self, **kwargs):
        p = self.get_parameter_options(kwargs['channel'])
        return self.ask(p['getfmt'])

    def set_visa_param(self, val, **kwargs):
        p = self.get_parameter_options(kwargs['channel'])
        return self.write(p['setfmt'] + str(val))

    def add_visa_parameter(self, name, getfmt, setfmt, **kwargs):
        kwargs['getfmt'] = getfmt
        kwargs['setfmt'] = setfmt
        self.add_parameter(name,
        get_func=self.get_visa_param, set_func=self.set_visa_param,
        channel=name, **kwargs)

    def close(self):
        if self.ins:
            self.ins.close()
        self.ins = None