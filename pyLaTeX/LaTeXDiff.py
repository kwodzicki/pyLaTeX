import os
from subprocess import Popen, DEVNULL, STDOUT

from pyLaTeX.utils.build import build

def LaTeXDiff(inFile, gitVersion, debug = False):
    tmp  = os.path.join('/tmp', '.tmpLaTeX.tex')
    dir  = os.path.dirname(inFile)
    base = os.path.basename(inFile)
    diff = '{}_track_changes{}'.format( *os.path.splitext(inFile) )
    print( 'Gettting old version...' )
    with open(tmp, 'w') as fid:
        proc = Popen( ['git', 'show', '{}:./{}'.format(gitVersion, base) ],
                    cwd = dir, stdout = fid)
        proc.wait()

    print( 'Running LaTeXDiff...' )
    with open(diff, 'w') as fid:
        proc = Popen( ['latexdiff', '--append-context2cmd=abstract', tmp, inFile], stdout = fid )
        proc.wait()

    os.remove( tmp )
    build( diff, debug = debug )

