import os
from subprocess import Popen, DEVNULL, STDOUT

from pyLaTeX.utils.build import build 
from pyLaTeX.LaTeX_2_docx import LaTeX_2_docx
from pyLaTeX.LaTeXDiff import LaTeXDiff

def LaTeX_Build_Doc(inFile, gitVersion = None, debug = False):
    inFile = os.path.realpath( inFile ) 
    build( inFile, debug = debug )
    if gitVersion is not None:
        LaTeXDiff( inFile, gitVersion, debug = debug )

    print('Creating docx file...')
    LaTeX_2_docx( inFile, debug = debug )


