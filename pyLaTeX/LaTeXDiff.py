import logging
import os
from subprocess import Popen, DEVNULL, STDOUT

from .utils import build

def LaTeXDiff(inFile, **kwargs):#gitVersion, debug = False):
  log  = logging.getLogger(__name__)
  if kwargs.get('gitVersion', None) is None:
    log.debug('No git version input, skipping LaTeXDiff')
    return
  
  gitVersion = kwargs.get('gitVersion')
  tmp        = os.path.join('/tmp', '.tmpLaTeX.tex')
  diff       = '{}_track_changes{}'.format( *os.path.splitext(inFile) )

  fileDir, fileBase  = os.path.split(inFile)

  log.info(  'Gettting old version...' )
  with open(tmp, 'w') as fid:
    proc = Popen( ['git', 'show', '{}:./{}'.format(gitVersion, fileBase) ],
                      cwd = fileDir, stdout = fid)
  proc.wait()

  log.info( 'Running LaTeXDiff...' )
  with open(diff, 'w') as fid:
    proc = Popen( ['latexdiff', '--append-context2cmd=abstract', tmp, inFile], stdout = fid )
    proc.wait()

  os.remove( tmp )
  build( diff, **kwargs )

