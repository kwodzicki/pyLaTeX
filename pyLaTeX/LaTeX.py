import logging
import os
import tempfile
from subprocess import Popen, STDOUT, DEVNULL

from .utils import recursiveRegex

class LaTeX( object ):
  LATEXDIFF = ['latexdiff', '--append-context2cmd=abstract']
  PDFLATEX  = ['pdflatex',  '-interaction=nonstopmode']
  XELATEX   = ['xelatex',   '-interaction=nonstopmode']
  BIBTEX    = ['bibtex']
  _infile   = None
  _lines    = None
  def __init__(self, infile):
    self.log = logging.getLogger(__name__)
    self.loadFile( infile )

  @property
  def infile(self):
    return self._infile
  @infile.setter
  def infile(self, val):
    if not val:
      raise Exception('Input file not defined')
    elif not os.path.isfile( val ):
      raise Exception('File does not exist')
    elif not val.endswith('.tex'):
      raise Exception('Invalid file exception')
    self._infile = os.path.abspath( val ) 

  def loadFile(self, infile):
    self.infile = infile
    with open(self.infile, 'r') as fid:
      self._lines = fid.read()
    return True

  def compile(self, infile = None, **kwargs):
    if not infile: infile = self.infile
    fileDir, fileBase = os.path.split(    infile )
    auxFile           = os.path.splitext( infile ) + '.aux'
    
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

  def _latexDiff(self, gitBranch = None, refFile = None):
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
      self.log.error('Must input git branch or reference file!')
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
      self.compile( infile = diff )


  def toDOCX( self, **kwargs ):
    fileDir = os.path.dirname( self.infile );
    fname, ext = os.path.splitext( self.infile )
    docx    = '{}.docx'.format( fname )
    md      = '{}.md'.format(   fname )
    lines   = LaTeX_crossref( lines=self._lines, returnLines = True );
    bibFile = self.getBibFile( )
    acroSub = replaceAcro( lines = self._lines );
    if acroSub.subAcros():
      lines = acroSub.lines;
  
    abstract = self.getAbstract( )
  
    if kwargs.get('debug', False):
      with open(file + '.txt', 'w') as f:
        for line in lines:
          f.write( line );
    base  = ['pandoc', '-f', 'latex', '-t', 'docx']
    opts  = ['--bibliography', bibFile] if bibFile is not None else [];
    files = ['-o', docx]
    
    try:
      p1 = Popen( ['echo', ''.join(lines)], stdout=PIPE)
      p2 = Popen( base + opts + files, cwd = filedir, stdin=p1.stdout)
      p1.stdout.close()
      p2.communicate()
      code = p2.returncode
    except:
      print('Pandoc command NOT found!!!')
      code = 127
    return code

  def getBibFile(self):
    res = recursiveRegex( r"\\bibliography", ("{", "}",) ).findall(self._lines)
    if len(res) == 1:
      bibFile = os.path.expandvars( res[0][1:-1] )                                # Convert bib from list to string
      if not bibFile.endswith('.bib'): bibFile += '.bib';                         # If the file path does NOT end wi
      return bibFile
    return None

  def getAbstract(self):
    res = recursiveRegex(r'\\abstract', ('{','}',)).findall( self._lines )
    if (len(res) == 1):
      return res[0][1:-1].splitlines()
    return None
