#!/usr/bin/env python

################################################################################
#  A small class to color output to a terminal.
#  Copyright (C) 2024  Alberto Mecca (alberto.mecca@cern.ch)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

class Colour:
    s_terminator = '\033[00m'
    s_white      = '\033[0;07m'
    s_red        = '\033[0;31m'    
    s_green      = '\033[0;32m'    
    s_yellow     = '\033[0;33m'    
    s_blue       = '\033[0;34m'    
    s_violet     = '\033[0;35m'    
    s_important  = '\033[0;41m'    
    s_ok         = '\033[0;42m'    
    s_warn       = '\033[0;43m'    
    s_evidence   = '\033[1;91;103m'

    def white    (st): return Colour.s_white     + str(st) + Colour.s_terminator
    def red      (st): return Colour.s_red       + str(st) + Colour.s_terminator
    def green    (st): return Colour.s_green     + str(st) + Colour.s_terminator
    def yellow   (st): return Colour.s_yellow    + str(st) + Colour.s_terminator
    def blue     (st): return Colour.s_blue      + str(st) + Colour.s_terminator
    def violet   (st): return Colour.s_violet    + str(st) + Colour.s_terminator
    def important(st): return Colour.s_important + str(st) + Colour.s_terminator
    def ok       (st): return Colour.s_ok        + str(st) + Colour.s_terminator
    def warn     (st): return Colour.s_warn      + str(st) + Colour.s_terminator
    def evidence (st): return Colour.s_evidence  + str(st) + Colour.s_terminator
