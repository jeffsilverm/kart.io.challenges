#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# This program generates an ensemble of colors for PuTTy
# The codes are documented in Wikipedia:
# https://en.wikipedia.org/wiki/ANSI_escape_code#DOS_and_Windows
# This list is not complete.

from __future__ import print_function

import sys

foreground = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37"
}

"""
Black	30	40	0,0,0	12,12,12	0,0,0	1,1,1
Red	31	41	170,0,0	128,0,0	197,15,31	194,54,33	187,0,0	127,0,0	205,0,
0	255,0,0	222,56,43
Green	32	42	0,170,0	0,128,0	19,161,14	37,188,36	0,187,0	0,147,0	0,205,
0	0,255,0	57,181,74
Yellow	33	43	170,85,0[nb 8]	128,128,0	238,237,240	193,156,0	173,173,
39	187,187,0	252,127,0	205,205,0	255,255,0	255,199,6
Blue	34	44	0,0,170	0,0,128	0,55,218	73,46,225	0,0,187	0,0,127	0,0,
238[23]	0,0,255	0,111,184
Magenta	35	45	170,0,170	128,0,128	1,36,86	136,23,152	211,56,211	187,0,
187	156,0,156	205,0,205	255,0,255	118,38,113
Cyan	36	46	0,170,170	0,128,128	58,150,221	51,187,200	0,187,187	0,
147,147	0,205,205	0,255,255	44,181,233
White	37	47
"""

background = dict()
for bgc in foreground.keys():  # background colors have the same names as
    # foreground colors
    fg_code = foreground[bgc]
    fg_color_int = int(fg_code)
    back_color_int = fg_color_int + 10
    back_color_code = str(back_color_int)
    background[bgc] = back_color_code

if "__main__" == __name__:
    for color in foreground.keys():
        for bgc in background.keys():
            padding = 10 - len(color)
            # I did it this way for maximum portability across versions
            sys.stdout.write("\033[%s;%smfg=%s bg=%s\033[0m"
                             % (foreground[color], background[bgc], color, bgc)\
                             + padding * ".")
        sys.stdout.write("\n")
    sys.stdout.write("\n")
