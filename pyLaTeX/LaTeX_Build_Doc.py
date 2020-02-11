import logging
import os
from subprocess import Popen, DEVNULL, STDOUT

from pyLaTeX.utils.build import build 
from pyLaTeX.LaTeX_2_docx import LaTeX_2_docx
from pyLaTeX.LaTeXDiff import LaTeXDiff

def LaTeX_Build_Doc(inFile, **kwargs):#gitVersion = None, debug = False):
  inFile = os.path.realpath( inFile ) 
  build( inFile, **kwargs  )
  LaTeXDiff( inFile, **kwargs )#gitVersion, debug = debug )
    
  LaTeX_2_docx( inFile, **kwargs )#debug = debug )


