#!/usr/bin/env python3

################################################################################
#  Compare two root files and highlight differeces in keys and contents of TH1
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

from argparse import ArgumentParser
import os
import re
from subprocess import run
from tempfile import NamedTemporaryFile
from enum import Enum
import logging
import ROOT

from mycolour import Colour
from rootutils import get_list_of_keys_deep

class ExitStatus(Enum):
    IDENTICAL         = 0
    # 1 is the interpreter's exit status for exceptions
    # 2                                      command line errors
    CLARG_ERROR       = 2
    INTERNAL_ERROR    = 3  # Something unexpected or not yet implemented
    EITHER_MISS       = 10 # either the first or the second is missing something
    FIRST_MISS        = 11
    SECOND_MISS       = 12
    DIFFERENCE_COMMON = 13 # This is bad


def compare_plot(h1, h2, verbosity=0, **kwargs):
    '''
    Detailed comparison of two TH1, bin by bin
    '''
    name = h1.GetName()

    printed_header = False
    def print_header():
        nonlocal printed_header
        if(not printed_header):
            print('#', name, '#')
            printed_header = True

    if( any([not h.Class().InheritsFrom('TH1') for h in (h1, h2)]) ):
        if(verbosity >= 1):
            print_header()
            print('\tNot histograms: h1 =', h1.ClassName(), ', h2 =', h2.ClassName())
        return

    if(not (h1.GetDimension() == h2.GetDimension()) ):
        print_header()
        print('\tDifferent dimensions:', h1.GetDimension(), h2.GetDimension())
        return

    ncells1 = h1.GetNcells()
    ncells2 = h2.GetNcells()
    if(not (ncells1 == ncells2) ):
        print_header()
        print('\tDifferent Ncells:', ncells1, ncells2)
        return

    # compare bin by bin
    print_wrong_plot = verbosity >= 2
    print_good_plot  = verbosity >= 4
    print_every_bin  = verbosity >= 3
    print_ok         = verbosity >= 5

    fmt_ncells = '{:%dd}' % ( len(str(ncells1)) )
    fmt = '\t'+fmt_ncells+': {:.3e} - {:.3e} - diff = {:+.3e}'

    ok_content = True

    for b in range(0, ncells1):
        c1 = h1.GetBinContent(b)
        c2 = h2.GetBinContent(b)
        if(c1 != c2):
            ok_content = False
            if(print_every_bin):
                print_header()
                print(fmt.format(b, c1, c2, c2-c1))
            else:
                break  # Don't need to continue

    if((print_wrong_plot or print_good_plot) and not print_every_bin):
        if(not ok_content):
            integral1 = h1.Integral(0, -1)
            integral2 = h2.Integral(0, -1)
            if(integral1 == integral2):
                print('{:48s} DIFFERENT!  But same integral: {:6.3g}'.format(name, integral1))
            else:
                print('{:48s} DIFFERENT!  Integral --> h1: {:6.3g} - h2: {:6.3g}  ({:+4.3g}%)'.format(name, integral1, integral2, 100*(integral2/integral1 - 1)))
        elif(print_good_plot):
            print('{:48s} equal     '.format(name)) #  ' Integrals --> h1: {:.2g} - h2: {:.2g}'.format(plot, h1.Integral(0, -1), h2.Integral(0, -1)))

    if(ok_content and print_ok):
        print_header()
        print('\tOK')

    return ok_content


def diff_full(keys1, keys2, **kwargs):
    with NamedTemporaryFile(mode='w') as temp1, NamedTemporaryFile(mode='w') as temp2:
        temp1.write('\n'.join(sorted(keys1))+'\n')
        temp2.write('\n'.join(sorted(keys2))+'\n')
        diff_proc = run(['diff', '--minimal', temp1.name, temp2.name], capture_output=True, encoding='utf-8')
        if(diff_proc.returncode == 2):
            print('ERROR in diff')
            exit(ExitStatus.INTERNAL_ERROR.value)
        print( diff_proc.stdout )
    return diff_proc.returncode


def get_fmt(a, b, tot):
    return '{:%dd}/{:%dd} ({:5.1f}) %%' % (
        max(
            len(str(a)),
            len(str(b))
        ),
        len(str(tot)),
    )


def print_missing(missing1, missing2, common, verbosity=0, **kwargs):
    print_every_plot        = verbosity >= 2
    print_every_plot_common = verbosity >= 4
    total = int( kwargs['total'] )
    fmt = get_fmt( len(missing1), len(missing2), total )

    if(len(missing1) > 0):
        print( Colour.red('Missing'), 'from 1:', fmt.format(len(missing1), total, 100*len(missing1)/total) )
        if(print_every_plot):
            for plot in sorted(missing1):
                print('\t'+plot)
            print()

    if(len(missing2) > 0):
        print( Colour.red('Missing'), 'from 2:', fmt.format(len(missing2), total, 100*len(missing2)/total) )
        if(print_every_plot):
            for plot in sorted(missing2):
                print('\t'+plot)
            print()

    if(len(common) > 0): # and ((len(missing1) > 0 or len(missing2) > 0) or verbosity >= 2)):
        print( Colour.green('Common'), 'in 1, 2:', fmt.format(len(common)  , total, 100*len(common  )/total) )
        if(print_every_plot_common):
            for plot in sorted(common):
                print('\t'+plot)
            print()


def print_content_status(content_status):
    ok  = content_status['OK']
    bad = content_status['BAD']
    tot = ok + bad

    if(tot == 0):
        print(Colour.warn('WARN')+'  nothing in common')
        return

    fmt = get_fmt(ok, bad, tot)

    print(Colour.green('Same content')+'  :', fmt.format(ok , tot, 100 * ok /tot))
    if(bad == 0):
        return
    print(Colour.red  ('Different')+'     :', fmt.format(bad, tot, 100 * bad/tot))


def diff_set(keys1, keys2, **kwargs):
    missing1 = keys2 - keys1
    missing2 = keys1 - keys2
    kwargs.setdefault('common', missing1 & missing2)

    print_missing(missing1, missing2, total=len(keys1|keys2), **kwargs)

    # NOTE: if any of the the common plots differ, this function won't detect it
    # This was made as a simpler implementation to test the more complicated print_missing
    if  (len(missing2) > 0):
        return ExitStatus.SECOND_MISS.value
    elif(len(missing2) > 0):
        return ExitStatus.FIRST_MISS.value
    else:
        ExitStatus.IDENTICAL.value


def parse_args():
    parser = ArgumentParser('Compare the content of two ROOT files, key by key')

    parser.add_argument('file1', metavar='FILE1')
    parser.add_argument('file2', metavar='FILE2')
    parser.add_argument('-p', '--plot'        , type=re.compile, help='Compare a specific plot; accepts a regexp')
    parser.add_argument(      '--plot-exclude', type=re.compile, help='Second regexp to exclude some of the selected plots')
    parser.add_argument(      '--diff', action='store_true', help='Use diff to compare the sorted lists of keys')
    parser.add_argument(      '--set' , action='store_true', help='Use the simpler comparison, which just checks if both files have the same keys')
    parser.add_argument('-v', '--verbose', dest='verbosity',
                        action='count', default=1,
                        help='increase verbosity')
    parser.add_argument('--verbosity', type=int,
                        metavar='LEVEL',
                        help='set verbosity')
    parser.add_argument('-q', '--quiet', dest='verbosity',
                        action='store_const', const=0,
                        help='set verbose to minimum')
    parser.add_argument('--log', dest='loglevel', metavar='LEVEL', default='WARNING', help='Level for the python logging module. Can be either a mnemonic string like DEBUG, INFO or WARNING or an integer (lower means more verbose).')

    return parser.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(format='%(levelname)s:%(module)s:%(funcName)s: %(message)s',
                        level=args.loglevel.upper() if not args.loglevel.isdigit() else int(args.loglevel))

    logging.info('args: %s', args)

    tf1 = ROOT.TFile(args.file1, 'READ')
    tf2 = ROOT.TFile(args.file2, 'READ')
    stat1 = os.fstat(tf1.GetFd())
    stat2 = os.fstat(tf2.GetFd())
    if(stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev):
        print('The two files are the same!')
        tf1.Close()
        tf2.Close()
        return ExitStatus.CLARG_ERROR.value

    logging.info('Extracting keys from file1...')
    keys1 = set(get_list_of_keys_deep(tf1))
    # keys1 = { k.GetName() for k in tf.GetListOfKeys() }

    logging.info('Extracting keys from file2...')
    keys2 = set(get_list_of_keys_deep(tf2))
    # keys2 = { k.GetName() for k in tf.GetListOfKeys() }

    logging.info('Now comparing keys')
    # Simpler implementations that check if both files have the same keys
    if  (args.diff):
        tf1.Close()
        tf2.Close()
        diff_retcode = diff_full(keys1, keys2, verbosity=args.verbosity)
        if(diff_retcode == 1):
            return ExitStatus.EITHER_MISS.value
        else:
            return ExitStatus.IDENTICAL.value
    elif(args.set):
        tf1.Close()
        tf2.Close()
        return diff_set(keys1, keys2, verbosity=args.verbosity)

    # Select keys
    matching_keys = keys1 | keys2
    print('Total keys =', len(matching_keys))

    if(args.plot is not None):
        matching_keys = { k for k in keys1|keys2 if args.plot.search(k)}
        if(len(matching_keys) == 0):
            tf1.Close()
            tf2.Close()
            print('ERROR: no keys matching', args.plot.pattern)
            return ExitStatus.CLARG_ERROR.value  # User specified a regex which does not match anything
        print('... of which matching regex', args.plot.pattern, '=', Colour.green(str(len(matching_keys))))

    if(args.plot_exclude is not None):
        # plot_exclude_regex_list = [re.compile(e) for e in args.plot_exclude]
        # matching_keys = { k for k in matching_keys if not any(exclude_regex.search(k) for exclude_regex in plot_exclude_regex_list)}
        matching_keys = { k for k in matching_keys if not args.plot_exclude.search(k) }
        if(len(matching_keys) == 0):
            tf1.Close()
            tf2.Close()
            print('ERROR: al keys excluded by', args.plot_exclude.pattern)
            return ExitStatus.CLARG_ERROR.value
        print('... of which not matching regex', args.plot_exclude.pattern, '=', Colour.green(str(len(matching_keys))))
    print()

    # Actual in-depth comparison of plots
    missing_keys = {1:matching_keys - keys1, 2: matching_keys - keys2}
    common_keys = matching_keys & keys1 & keys2

    content_status = {'OK': 0, 'BAD': 0}

    if(True):
        for plot in sorted(common_keys):
            h1 = tf1.Get(plot)
            h2 = tf2.Get(plot)
            assert h1 and h2, 'Unable to retrieve both plots "'+plot+'" from the files'
            ok_content = compare_plot(h1, h2, verbosity=args.verbosity)
            if(ok_content): content_status['OK']  += 1
            else          : content_status['BAD'] += 1

    tf1.Close()
    tf2.Close()

    print_missing(missing_keys[1], missing_keys[2], common=common_keys, verbosity=args.verbosity, total=len(matching_keys))
    print()
    print_content_status(content_status)

    if  (content_status['BAD'] > 0):
        return ExitStatus.DIFFERENCE_COMMON.value
    elif(len(missing_keys[2]) > 0):
         return ExitStatus.SECOND_MISS.value
    elif(len(missing_keys[1]) > 0):
        return ExitStatus.FIRST_MISS.value
    else:
        return ExitStatus.IDENTICAL.value


if __name__ == '__main__':
    exit(main())
