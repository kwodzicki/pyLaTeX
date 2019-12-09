import os
from subprocess import Popen, DEVNULL, STDOUT

def build(inFile, debug = False):
    buildDir = os.path.dirname(inFile)
    auxFile  = os.path.splitext(inFile)[0] + '.aux'
    pdfLaTeX = ['pdflatex', '-interaction=nonstopmode', os.path.basename( inFile )]
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
