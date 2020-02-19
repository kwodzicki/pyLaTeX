import logging
import os
import tempfile
from subprocess import Popen, PIPE, STDOUT, DEVNULL

from .acronyms import Acronyms
from .crossref import CrossRef
from .utils import recursiveRegex, removeComments

ENVIRONS = [CrossRef('Figure', 'figure', 'warpfigure'),
            CrossRef('Table',  'table'),
            CrossRef('eq',     'equation')]

class LaTeX( Acronyms ):
  LATEXDIFF = ['latexdiff', '--append-context2cmd=abstract']
  PDFLATEX  = ['pdflatex',  '-interaction=nonstopmode']
  XELATEX   = ['xelatex',   '-interaction=nonstopmode']
  BIBTEX    = ['bibtex']

  def compile(self, infile = None, **kwargs):
    if not infile: infile = self.infile
    fileDir, fileBase = os.path.split(    infile )
    auxFile           = os.path.splitext( infile )[0] + '.aux'
    
    if kwargs.get('xelatex', False):
      latex = self.XELATEX + [fileBase]
    else:
      latex = self.PDFLATEX + [fileBase]
    bibtex = self.BIBTEX + [os.path.basename(auxFile)]

    kwargsCMD = {'cwd' : fileDir, 'stdout' : DEVNULL, 'stderr' : STDOUT}    
    if kwargs.get('debug', False):
      kwargsCMD['stdout'] = None
      kwargsCMD['stderr'] = None

    self.log.info('Compiling TeX file: {}'.format(infile) )
    cmds = [latex, bibtex, latex, latex]
    for cmd in cmds:
      proc = Popen( cmd, **kwargsCMD )
      proc.wait()
      if proc.returncode != 0:
        self.log.error( 'There was an error compiling: {}'.format(cmd) )
        return False

  def trackChanges(self, **kwargs): 
    '''
    Purpose:
      Method for creating tracked changes using the latexdiff CLI
    Inputs:
      None.
    Keywords:
      getBranch  : Git branch where old, reference version is saved
      refFile  : Full path to old, reference file.
    Returns:
      None, but a tracked changes file will be created
    '''
    diff = self._latexDiff( **kwargs )
    if diff:
      self.compile( infile = diff, **kwargs)


  def toDOCX( self, **kwargs ):
    fileDir = os.path.dirname( self.infile );
    fname, ext = os.path.splitext( self.infile )
    docx    = '{}.docx'.format( fname )
    md      = '{}.md'.format(   fname )
    text    = removeComments( self._text )
    for env in ENVIRONS:
      text = env.process(text)

    self.subAcros()
  
    abstract = self.getAbstract( text )
  
    if kwargs.get('debug', False):
      with open(self.infile + '.txt', 'w') as fid:
        fid.write( text );    

    try:
      p1 = Popen( ['echo', text], stdout=PIPE)
      p2 = Popen( self._pandoc(docx), cwd = fileDir, stdin=p1.stdout)
      p1.stdout.close()
      p2.communicate()
      code = p2.returncode
    except Exception as err:
      print( err )
      print('Pandoc command NOT found!!!')
      code = 127
    return code

  def _latexDiff(self, gitBranch = None, refFile = None, **kwargs):
    '''
    Purpose:
      Method for creating tracked changes using the latexdiff CLI
    Inputs:
      None.
    Keywords:
      getVers  : Git branch where old, reference version is saved
      refFile  : Full path to old, reference file.
    Returns:
      None, but a tracked changes tex file will be created
    '''
    if gitBranch:
      self.log.info('Getting old version from git branch: {}'.format(gitBranch) )
      base = os.path.basename(self.infile)
      fid  = tempfile.NamedTemporaryFile( suffix='.tex', delete=False )
      proc = Popen( ['git', 'show', '{}:./{}'.format(gitBranch, base)],
                    cwd = os.path.dirname(self.infile), stdout = fid)
      proc.wait()
      fid.close()
      refFile = fid.name
    elif not refFile:
      return False
 
    self.log.info('Runing latexdiff')
    diff = '{}_track_changes{}'.format( *os.path.splitext(self.infile) )

    with open(diff, 'w') as fid:
      proc = Popen( self.LATEXDIFF + [refFile, self.infile], stdout = fid )
      proc.wait()

    if gitBranch:
      self.log.debug('Removing temporary file: {}'.format(refFile) )
      os.remove( refFile )

    if proc.returncode == 0:
      return diff
    else:
      self.log.error('There was an error running latexdiff')
      return False
 
