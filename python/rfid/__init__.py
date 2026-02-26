#
# Copyright 2023 Xin Liu.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

'''GNU Radio RFID module — EPC Gen2 UHF RFID reader.'''
import os

# import pybind11 generated symbols into the rfid namespace
try:
    from .rfid_python import *
except ModuleNotFoundError:
    pass
