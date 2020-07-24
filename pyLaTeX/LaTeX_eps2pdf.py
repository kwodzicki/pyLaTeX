#!/usr/bin/env python

import sys, os
from subprocess import call

if (len(sys.argv) != 2): 
    print('Must input directory!')
    exit(1)

newFMT  = '{}-{}-converted-to.pdf'
cmdBase = ['ps2pdf', '-dEPSCrop']

inDir   = sys.argv[1]
for file in os.listdir( inDir ):
    if file.endswith('.ps') or file.endswith('.eps'):
        inFile        = os.path.join( inDir, file ) 
        inName, inExt = os.path.splitext( file )
        newFile       = newFMT.format( inName, inExt[1:] )
        outFile       = os.path.join( inDir, newFile )
        result        = call( cmdBase + [inFile, outFile] )
        
exit(0)
