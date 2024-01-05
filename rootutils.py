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
                yield get_keys_in_folder(k.ReadObj(), path=newpath)
            else:
                yield os.path.join(path, k.GetName())

    for k in tfile.GetListOfKeys():
        # logging.debug('key: %s', k.GetName())
        if k.IsFolder():
            yield from get_keys_in_folder(k.ReadObj(), path=k.GetName())
        else:
            yield k.GetName()
