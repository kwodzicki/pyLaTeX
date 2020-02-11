import logging
import os
from subprocess import Popen, DEVNULL, STDOUT

def build(inFile, **kwargs):
  log      = logging.getLogger(__name__)
  buildDir = os.path.dirname(inFile)
  auxFile  = os.path.splitext(inFile)[0] + '.aux'
  LaTeXCMD = 'xelatex' if kwargs.get('xelatex', False) else 'pdflatex'
  LaTeXCMD = [LaTeXCMD, '-interaction=nonstopmode', os.path.basename( inFile )]
  bibTex   = ['bibtex',   os.path.basename( auxFile )]

  kwargsCMD = {'cwd'    : buildDir,
               'stdout' : DEVNULL,
               'stderr' : STDOUT}
  if kwargs.get('debug', False):
    kwargsCMD['stdout'] = None
    kwargsCMD['stderr'] = None

  log.info( 'Compiling TeX file: {}'.format( inFile ) )
  cmds     = [LaTeXCMD, bibTex, LaTeXCMD, LaTeXCMD]
  for cmd in cmds:
    proc = Popen( cmd, **kwargsCMD )
    proc.wait()
