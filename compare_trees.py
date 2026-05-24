#!/usr/bin/env python
from argparse import ArgumentParser
import logging
from array import array
import numpy as np

import ROOT


def main(args):
    logging.debug('args: %s', args)

    # Declare helper functions
    ROOT.gInterpreter.Declare('using ROOT::VecOps::RVec;')
    # continuous: relative difference, special case for 0
    for ct in ('Double_t', 'Float_t'):
        s = 'int compare_scalars({0:s} a, {0:s} b) {{ return fabs(a!=0 ? b/a-1 : b) > {1:f}; }}'.format(ct, args.threshold)
        # logging.debug(s)
        ROOT.gInterpreter.Declare(s)
    # discrete: exact equality
    for ct in ('ULong64_t', 'Int_t', 'UInt_t', 'Short_t', 'Bool_t'):
        s = 'int compare_scalars({0} a, {0} b) {{ return b != a; }}'.format(ct)
        # logging.debug(s)
        ROOT.gInterpreter.Declare(s)

    # template function for vectors: check the size, then each element
    ROOT.gInterpreter.Declare('''\
template <class T>
int compare_vectors(const RVec<T>& v, const RVec<T>& u) {
  if(v.size() != u.size()) {
    return 1;
  }

  for(size_t i=0; i<v.size(); ++i) {
    if(compare_scalars(v[i], u[i])) return 1;
  }

  return 0;
}''')

    tf1 = ROOT.TFile(args.file1)
    tf2 = ROOT.TFile(args.file2)
    tree_ref = tf1.Get(args.tree1)
    tree_new = tf2.Get(args.tree2)
    for t, n, f in [[tree_ref, args.tree1, args.file1], [tree_new, args.tree2, args.file2]]:
        if(not t):
            logging.critical('Could not load TTree "%s" from "%s"', n, f)
            return 2
    logging.debug('Opened files and loaded trees')

    # First test: number of entries (failure does not halt the rest ot the tests)
    n_ref = tree_ref.GetEntries()
    n_new = tree_new.GetEntries()
    if(n_new != n_ref): logging.error('different number of entries: %d and %d', n_ref, n_new)

    # We need to join the two datasets to compare them.
    # Unfortunately, ROOT provides no helper to join two RDF horizontally.
    # TTrees can AddFriend() though, so we build the RDF after joining the trees;
    # their files must stay open until we use them.
    tree_ref.AddFriend(tree_new, PRFNEW, True)
    df = ROOT.RDataFrame(tree_ref)

    columns = [str(c) for c in df.GetColumnNames() if not str(c).startswith(PRFNEW)]
    logging.info('comparing %d columns', len(columns))

    if(args.nentries > 0):
        logging.info('Will run only on the first %d entries', args.nentries)
        df = df.Range(args.nentries)
    else:
        logging.info('The trees have %d entries', n_ref)

    counts = []
    for col_n in columns:
        col_t = df.GetColumnType(col_n)
        new_col_n = PRFNEW+'.'+col_n
        new_col_t = df.GetColumnType(new_col_n)
        logging.debug('column %-8s %s -> %-8s %s', col_t, col_n, new_col_t, new_col_n)
        if(new_col_t != col_t):
            logging.error('Column "%s" has different type: %s -> %s', col_n, col_t, new_col_t)
            has_diff += 1
            continue

        diff_n = PRFDIF+col_n

        # Vectors:
        if 'RVec' in col_t:
            df_diff = df.Define(diff_n, 'compare_vectors({1}, {0})'.format(col_n, new_col_n))
        else:
            df_diff = df.Define(diff_n, 'compare_scalars({1}, {0})'.format(col_n, new_col_n))

        n = df_diff.Filter('%s != 0' %(diff_n)).Count()
        counts.append(dict(col_n=col_n, col_t=col_t, n=n))

    has_diff = 0
    for c in counts:
        if(c['n'].GetValue() > 0):
            logging.error('Found difference in column "%s" (%s)', c['col_n'], c['col_t'])
            has_diff += 1

    tf1.Close()
    tf2.Close()
    logging.info('Found differences in %d columns', has_diff)

    return 0 if has_diff == 0 else 1


def parse_args():
    parser = ArgumentParser('Compare the contents TTrees, possibly in different files')
    parser.add_argument('filetree1', metavar='FILE:TREE', help='":TREE" is optional if --tree is specified.')
    parser.add_argument('filetree2', metavar='FILE:TREE')
    parser.add_argument('-t', '--tree', default='Events', help='Name of the tree in the files. Overridden with FILE:TREE. Default: %(default)s.')
    parser.add_argument('-n', '--nentries', metavar='N', type=int, default=0, help='Number of entries to process (default: %(default)s).')
    parser.add_argument(      '--threshold', metavar='TOL', type=lambda x: abs(float(x)), default=1e-6, help='Maximum allowed fracional difference (default: %(default)g)')
    parser.add_argument('--log', dest='loglevel', metavar='LEVEL', default='WARNING', help='Level for the python logging module. Can be either a mnemonic string like DEBUG, INFO or WARNING or an integer (lower means more verbose).')

    args = parser.parse_args()

    s1 = args.filetree1.split(':')
    s2 = args.filetree2.split(':')
    args.file1 = s1[0]
    args.file2 = s2[0]
    args.tree1 = s1[1] if len(s1) > 1 else args.tree
    args.tree2 = s2[1] if len(s2) > 1 else args.tree
    del args.tree
    del args.filetree1
    del args.filetree2

    return args


PRFNEW = "_new_"
PRFDIF = "_diff_"


def config_logging(loglevel):
    loglevel = loglevel.upper() if not loglevel.isdigit() else int(loglevel)
    logging.basicConfig(format='%(levelname)s:%(module)s:%(funcName)s: %(message)s', level=loglevel)


if __name__ == '__main__':
    args = parse_args()
    config_logging(args.loglevel)
    exit(main(args))
