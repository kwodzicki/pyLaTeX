import logging
import os, re
import tempfile
from subprocess import Popen, PIPE, STDOUT, DEVNULL

from .acronyms import Acronyms
from .crossref import CrossRef
from .utils import removeComments 

ENVIRONS = [CrossRef('Figure', 'figure', 'warpfigure'),
            CrossRef('Table',  'table'),
            CrossRef('eq',     'equation')]

def auxCheck(*args, oldData = None):
  data = {}
  for auxFile in args:
    if os.path.isfile(auxFile):
      with open(auxFile, 'r') as fid:
        data[auxFile] = fid.read()
  if oldData:
    return data == oldData
  return data 

class LaTeX( Acronyms ):
  LATEXDIFF = ['latexdiff', '--append-context2cmd=abstract']
  PDFLATEX  = ['pdflatex',  '-interaction=nonstopmode']
  XELATEX   = ['xelatex',   '-interaction=nonstopmode']
  BIBTEX    = ['bibtex']

  def findAuxFiles(self):
    aux = []
    for root, dirs, items in os.walk( os.path.dirname(self.infile) ):
      for item in items:
        if item.endswith('.aux'):
          aux.append( os.path.join( root, item ) )
    return aux

  def compile(self, infile = None, **kwargs):
    if not infile: infile = self.infile
    fileDir, fileBase = os.path.split(    infile )
    auxFiles = self.findAuxFiles()
    self.log.debug( 'Aux file(s): {}'.format(auxFiles) )
    oldData  = auxCheck( *auxFiles )

    if kwargs.get('xelatex', False):                                            # If the xelatex keyword is set
      latex = self.XELATEX + [fileBase]                                         # Use xelatex
    elif re.search('{fontspec}|{mathspec}', self._text) is not None:            # Else, if {fontspec} or {mathspec} found in text
      latex = self.XELATEX + [fileBase]                                         # Use xelatex
    else:                                                                       # Else
      latex = self.PDFLATEX + [fileBase]                                        # Use pdf latex
    bibtex = [self.BIBTEX + [os.path.basename(aux)] for aux in auxFiles]        # Set bibtex command

    kwargsCMD = {'cwd' : fileDir, 'stdout' : DEVNULL, 'stderr' : STDOUT}    
    if kwargs.get('debug', False):
      kwargsCMD['stdout'] = None
      kwargsCMD['stderr'] = None

    self.log.info('Compiling TeX file: {}'.format(infile) )
    cmds = [latex, *bibtex, latex, latex]
    for i, cmd in enumerate(cmds):
      self.log.debug('Running command: {}'.format( cmd ))
      proc = Popen( cmd, **kwargsCMD )
      proc.wait()
      if self.BIBTEX[0] not in cmd and proc.returncode != 0:
        self.log.error( 'There was an error compiling: {}'.format(cmd) )
        return False
      elif (i == 0) and auxCheck(*auxFiles, oldData=oldData) is True:
        self.log.debug('Aux file(s) unchaged, no need for long compile')
        break

    if kwargs.get('with_bbl', False):
      self._insertBib()

  def trackChanges(self, **kwargs): 
    """
    Create tracked changes using the latexdiff CLI

    Arguments:
      None.

    Keyword arguments:
      getBranch  : Git branch where old, reference version is saved
      refFile  : Full path to old, reference file.

    Returns:
      None: but a tracked changes file will be created

    """

    diff = self._latexDiff( **kwargs )
    if diff:
      self.compile( infile = diff, **kwargs)

  def exportTo(self, **kwargs):
    fname, ext = os.path.splitext( self.infile )																# Get extensionless file path
    text    = removeComments( self._text )																			# Remove comments for
    bibFile = self.getBibFile(text)																							# Get bibliography file name
    docx    = '{}.docx'.format( fname ) if kwargs.get('docx',     False) else None
    md      = '{}.md'.format(   fname ) if kwargs.get('markdown', False) else None
    if md or docx:
      md = self._toMarkdown(text=text, outFile=md, bibFile=bibFile)
      if docx:
        self._toDOCX(docx, text=md, bibFile=bibFile)
 
  def _toDOCX( self, outFile, **kwargs ):
    self.log.debug('Converting to docx...')
    text = kwargs.get('text', None)
    if text is None:
      text = self._toMarkdown(**kwargs)

    kwargs['srcfmt'] = 'markdown'
    pandoc = self._pandoc(outFile=outFile, **kwargs) 
    try:
      p1 = Popen( ['echo', text], stdout=PIPE)
      p2 = Popen( pandoc, cwd = os.path.dirname(outFile), stdin=p1.stdout)
      p1.stdout.close()
      p2.communicate()
    except Exception as err:
      self.log.error( err )
      return False
    return True

  def _toMarkdown( self, **kwargs ):
    """
    Method to convert LaTeX to pandoc markdown format

    Arguments:
      None.

    Keyword arguments:
      text    : Text to process; default is to used text from file
      outFile : Path to output file for saving data; default
                 is to not write data to disk
    Returns:
      Returns string containing converted text

    """ 
    fileDir = os.path.dirname( self.infile );
    text    = kwargs.get('text', removeComments( self._text ))
    for env in ENVIRONS:
      text = env.process(text)

    text     = self.subAcros(   text )
    text     = self.insertAbstract(text)
    title    = self.getTitle(   text ) 
    authors  = self.getAuthors( text )
    metadata = '%{}\n%{}\n\n'.format(title, authors)

    outFile = kwargs.pop('outFile', None)
    kwargs['destfmt'] = 'markdown'
    pandoc = self._pandoc(**kwargs)
    try:
      p1 = Popen( ['echo', text], stdout=PIPE)
      p2 = Popen( pandoc, cwd = fileDir, stdin=p1.stdout, stdout=PIPE)
      p1.stdout.close()
      stdout = p2.stdout.read()
      p2.communicate()
      code = p2.returncode
    except Exception as err:
      self.log.error( err )
      return None
    stdout  = metadata + stdout.decode()
    if outFile is not None:
      with open(outFile, 'w') as fid:
        fid.write( stdout )
    return stdout

  def _latexDiff(self, gitBranch = None, refFile = None, **kwargs):
    """
    Method for creating tracked changes using the latexdiff CLI

    Arguments:
      None.

    Keyword arguments:
      getVers  : Git branch where old, reference version is saved
      refFile  : Full path to old, reference file.

    Returns:
      None: Tracked changes tex file will be created

    """
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
