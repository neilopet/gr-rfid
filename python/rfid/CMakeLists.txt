# Copyright 2011 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Include python install macros
########################################################################
include(GrPython)
if(NOT PYTHONINTERP_FOUND)
    return()
endif()

add_subdirectory(bindings)

########################################################################
# Install python sources
########################################################################
gr_python_install(FILES __init__.py DESTINATION ${GR_PYTHON_DIR}/gnuradio/rfid)
