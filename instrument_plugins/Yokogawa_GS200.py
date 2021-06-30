
import numpy as np
from instrument import Instrument, VisaInstrument


class yokogawa_GS200(VisaInstrument):

    def __init__(self, name, **kwargs):
        super(yokogawa_GS200, self).__init__(name, **kwargs)

        self.add_visa_parameter('Voltage',
            'SOUR:LEV? ', 'SOUR:LEV ', type=float, range=[0, ],
            step=0.00001)
        