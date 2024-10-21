#!/bin/sh

################################################################################
#  Simple script to extract integral from histograms in rootfiles
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

show_help(){ cat <<EOF
Usage: ${0##*/} [-u] FILE HIST [BIN]"
Get integral of histogram HIST from root file FILE.
If BIN is specified, only its value is extracted.

    -h      show help and exit
    -a      include under/overflow
    -b	    yield for each bin
    -l 	    use alphanumeric labels
EOF
}

show_all=false
by_label=false
by_bin=false
OPTIND=1
while getopts "habl" opt; do
    case $opt in
        h)
            show_help
            exit 0
            ;;
        a)
            show_all=true
            ;;
	b)
	    by_bin=true
	    ;;
	l)
	    by_label=true
	    ;;
        # r)
        #     [ "$OPTARG" -eq "$OPTARG" ] || exit 2
        #     mu=$OPTARG
        #     ;;
        *)
            show_help >&2
            exit 1
            ;;
    esac
done
shift "$((OPTIND-1))"

[ $# -ge 2 ] || { show_help >&2 ; exit 1 ; }
[ -f "$1" ] || { echo "$1 does not exist or is not a file" >&2 ; exit 2 ; }
if $show_all ; then
    bmin=0
    bmax="h->GetNbinsX()+1"
else
    bmin=1
    bmax="h->GetNbinsX()"
fi
basecmd='h = ((TH1*)_file0->Get("'"$2"'")); if(!h){ printf("Missing histogram \"'"$2"'\"\n"); exit(1); };'

if [ $# -eq 2 ] ; then
    # No bin was specified
    if $by_bin ; then
	# Show the yield in each bin
	if $by_label ; then
	    root -l "$1" -e \
		 "$basecmd"' for(int b = '$bmin'; b <= '$bmax'; ++b) { printf("%-16s: %f +- %f\n", h->GetXaxis()->GetBinLabel(b), h->GetBinContent(b), h->GetBinError(b)); } return 0;' \
		 -q
	else
	    root -l "$1" -e \
		 "$basecmd"' for(int b = '$bmin'; b <= '$bmax'; ++b) { printf("%d: %f +- %f\n", b, h->GetBinContent(b), h->GetBinError(b)); } return 0;' \
		 -q
	fi
    else
	# Just show integral
	root -l "$1" -e \
	     "$basecmd"' double i(0.), e(0.); i = h->IntegralAndError('$bmin', '$bmax', e); printf("%f +- %f\n", i, e); return 0;' \
	     -q
    fi
else
    $show_all && echo "WARN: a specific bin was supplied, ignoring \"-a\"" 2>&1
    # Show a specific bin
    if $by_label ; then
	root -l "$1" -e \
	     "$basecmd"' int bin = h->GetXaxis()->FindFixBin("'"$3"'"); printf("%f += %f\n", h->GetBinContent(bin), h->GetBinError(bin)); return 0;' \
	     -q
    else
	root -l "$1" -e \
	     "$basecmd"' printf("%f +- %f\n", h->GetBinContent('"$3"'), h->GetBinError('"$3"')); return 0;' \
	     -q
    fi
fi
