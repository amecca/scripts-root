################################################################################
#  Utilities for compare_rootfiles.py
#  Copyright (C) 2025  Alberto Mecca (alberto.mecca@cern.ch)
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

import subprocess


class CompletedProcessPy2:
    def __init__(self, args, returncode, stdout, stderr):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def check_returncode():
        if(self.returncode != 0):
            raise subprocess.CalledProcessError(
                "Command '%s' returned non-zero exit status %d." %(args, self.returncode)
            )


def subprocess_run(args, *args_l, **kwargs):
    '''
    Emulates subprocess.run in py2.
    This simple implementation passes everything to Popen
    '''

    # Massage kwargs for Popen
    # WARNING: we do not handle the case where these were passed by position
    # One has to be quite mad already to pass them by position to subprocess.run
    # so this should happen rarely
    kwargs.pop('capture_output', None)
    kwargs.update('stdout', subprocess.PIPE)
    kwargs.update('stderr', subprocess.PIPE)

    p = subprocess.Popen(args, *args_l, **kwargs)
    out, err = p.communicate()
    ret = p.wait()

    return CompletedProcessPy2(args=args, returncode=ret, stdout=out, stderr=err)
