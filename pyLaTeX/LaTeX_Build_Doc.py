#!/usr/bin/env python
import os
from subprocess import Popen, DEVNULL, STDOUT

from LaTeX.LaTeX_2_docx import LaTeX_2_docx

def build(inFile, debug = False):
    buildDir = os.path.dirname(inFile)
    auxFile  = os.path.splitext(inFile)[0] + '.aux'
    pdfLaTeX = ['pdflatex', os.path.basename( inFile )]
    bibTex   = ['bibtex',   os.path.basename( auxFile )]

    kwargs = {'cwd'    : buildDir,
              'stdout' : DEVNULL,
              'stderr' : STDOUT}
    if debug:
        kwargs['stdout'] = None
        kwargs['stderr'] = None

    print( 'Compiling TeX file: {}'.format( inFile ) )
    cmds     = [pdfLaTeX, bibTex, pdfLaTeX, pdfLaTeX]
    for cmd in cmds:
        proc = Popen( cmd, **kwargs )
        proc.wait()

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
        proc = Popen( ['latexdiff', tmp, inFile], stdout = fid )
        proc.wait()

    os.remove( tmp )
    build( diff, debug = debug )

def LaTeX_Build_Doc(inFile, gitVersion = None, debug = False):
    build( inFile, debug = debug )
    if gitVersion is not None:
        LaTeXDiff( inFile, gitVersion, debug = debug )

    print('Creating docx file...')
    LaTeX_2_docx( inFile, debug = debug )



if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        LaTeX_Build_Doc( os.path.realpath(sys.argv[1]), sys.argv[2],
            debug = len(sys.argv) == 4 )
