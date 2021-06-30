from importlib import import_module
from inspect import getmembers, isclass
import logging
from outputwidgethandler import OutputWidgetHandler

settings_path = r'C:\Users\physt\instruments\settings'
plugins_dir = r'instrument_plugins'


class InstrumentsManager(object):

    def __init__(self, **kwargs):

        self.visa_rm = None
        self.visa_addrs = None
        self.instruments = {}

        self.logger = logging.getLogger(__name__)
        if 'logname' not in kwargs:
            self.handler = OutputWidgetHandler('debug.log', mode='w')
        else:
            self.handler = OutputWidgetHandler(kwargs['logname'], mode='w')
        self.handler.setFormatter(logging.Formatter('%(asctime)s, %(threadName)s, [%(levelname)s] %(message)s'))
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def set_visa_rm(self, rm):

        self.visa_rm = rm
        self.visa_addrs = rm.list_resources()

    def create_visa_instrument(self, name, model, addr):
        ins_module = import_module('%s.%s' % (plugins_dir, model))
        ins_classes = getmembers(ins_module, isclass)
        ins = [item for item in ins_classes if item[0].lower() \
               == model.lower()][0][1]
        self.instruments[str(name)] = ins(str(name), logger=self.logger)
        self.instruments[str(name)].logger.info(str(ins))
        self.instruments[str(name)].create_visa_instrument(self.visa_rm,
                                                           str(model), addr)
