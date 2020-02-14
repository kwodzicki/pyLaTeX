import logging
import os

from .utils import build 
from .LaTeX_2_docx import LaTeX_2_docx
from .LaTeXDiff import LaTeXDiff

def LaTeX_Build_Doc(inFile, **kwargs):#gitVersion = None, debug = False):
  inFile = os.path.realpath( inFile ) 
  build( inFile, **kwargs  )
  LaTeXDiff( inFile, **kwargs )#gitVersion, debug = debug )
    
  if kwargs.get('docx', False):
    LaTeX_2_docx( inFile, **kwargs )#debug = debug )


