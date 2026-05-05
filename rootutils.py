#!/usr/bin/env python

################################################################################
#  Utilities for ROOT objects.
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

import os
from ctypes import c_double
import ROOT

class TFileContext(object):
    def __init__(self, *args):
        self.tfile = ROOT.TFile(*args)
    def __enter__(self):
        return self.tfile
    def __exit__(self, type, value, traceback):
        self.tfile.Close()

def get_list_of_keys_deep(tfile):
    '''
    Recursively search the TDirectories of a ROOT file and yield the paths to each key.
    The search is performed depth-first
    '''
    def get_keys_in_folder(tfolder, path=''):
        # logging.debug('tfolder: "%s", path so far: "%s"', tfolder.GetName(), path)
        for k in tfolder.GetListOfKeys():
            if(k.IsFolder()):
                newpath = os.path.join(path, k.GetName())
                # logging.debug('Recursing "%s", newpath: "%s"', k.GetName(), newpath)

                # We would really like to use yield from, but we need to be compatible with python2...
                for k in get_keys_in_folder(k.ReadObj(), path=newpath): yield k
            else:
                yield os.path.join(path, k.GetName())

    for k in tfile.GetListOfKeys():
        # logging.debug('key: %s', k.GetName())
        if k.IsFolder():
            # Python2 equivalent of "yield from"
            for k in get_keys_in_folder(k.ReadObj(), path=k.GetName()): yield k
        else:
            yield k.GetName()


def TH_integr_and_err(h : ROOT.TH1, ranges : list[list[int]] = None):
    assert h.Class().InheritsFrom('TH1'), 'Unexpected type <%s>' %(h.Class().GetName())
    if ranges is None:
        ranges = [0, -1]*h1.GetDimension()

    c_err = c_double(0.)
    integr = h.IntegralAndError(*ranges, c_err)

    return integr, c_err.value
