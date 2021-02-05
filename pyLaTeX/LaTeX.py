import logging
import os, re
import tempfile
from subprocess import Popen, PIPE, STDOUT, DEVNULL

from . import VERSIONS
from .acronyms import Acronyms
from .crossref import CrossRef
from .utils import removeComments 

# Environments for cross referencing
ENVIRONS = [CrossRef('Figure', 'figure', 'warpfigure'),
            CrossRef('Table',  'table'),
            CrossRef('eq',     'equation')]

def auxCheck(*args, oldData = None):
  """
  Check if aux file(s) has changed

  This function will read in all the data from aux files and store
  the data in a dictionary where keys are the file names/paths and
  the values are the data.

  If the oldData is used, then the data read in from the aux files
  is checked against the oldData. If the data are equal, then the
  aux files have not changed, so there is no need for a long recompile

  Arguments:
    *args : Any number of paths to auxFiles

  Keyword arguments:
    oldData (dict): If input, will check if newly read aux file data
      matches data in the dictionary

  Returns:
    dict, bool: If the oldData keyword is NOT used, then a dict 
      containing the data from the aux files is returned. If the
      oldData keyword IS used, then returns a bool of whether the
      oldData matches the new data.

  """

  data = {}                                                                     # Dict for storing aux file data
  for auxFile in args:                                                          # Iterate over all arguments
    if os.path.isfile(auxFile):                                                 # If the path is a file
      with open(auxFile, 'r') as fid:                                           # Open file for reading
        data[auxFile] = fid.read()                                              # Store file data in data dict
  if isinstance(oldData, dict):                                                 # If oldData is a dict 
    return data == oldData                                                      # Return bool of whether data and oldData match
  return data                                                                   # Return data

class LaTeX( Acronyms ):
  LATEXDIFF = ['latexdiff', '--append-context2cmd=abstract']
  PDFLATEX  = 'pdflatex'
  XELATEX   = 'xelatex'
  BIBTEX    = ['bibtex']
  TEXOPTS   = ['-interaction=nonstopmode'] 

  def _bibtex(self, auxFiles):
    return [self.BIBTEX + [os.path.basename(aux)] for aux in auxFiles]        # Set bibtex command

  def _call(self, cmd, **kwargs):
    self.log.debug('Running command: {}'.format( cmd ))
    proc = Popen( cmd, **kwargs )
    proc.wait()
    return proc

  def findAuxFiles(self):
    aux = []
    for root, dirs, items in os.walk( os.path.dirname(self.infile) ):
      for item in items:
        if item.endswith('.aux'):
          aux.append( os.path.join( root, item ) )
    return aux

  def compile(self, infile = None, texlive = 'Latest', **kwargs):
    if not infile: infile = self.infile
    fileDir, fileBase = os.path.split(    infile )
    auxFiles = self.findAuxFiles()
    self.log.debug( 'Aux file(s): {}'.format(auxFiles) )
    oldData  = auxCheck( *auxFiles )

    if texlive not in VERSIONS: texlive = 'Latest'
    path = VERSIONS[texlive]

    if kwargs.get('xelatex', False):                                            # If the xelatex keyword is set
      latex = [ os.path.join(path, self.XELATEX)] + self.TEXOPTS + [fileBase]   # Use xelatex
    elif re.search('{fontspec}|{mathspec}', self._text) is not None:            # Else, if {fontspec} or {mathspec} found in text
      latex = [ os.path.join(path, self.XELATEX)] + self.TEXOPTS + [fileBase]   # Use xelatex
    else:                                                                       # Else
      latex = [ os.path.join(path, self.PDFLATEX)] + self.TEXOPTS + [fileBase]  # Use xelatex
    bibtex = self._bibtex( auxFiles )                                           # Set bibtex command; if there were no aux files found, this will be empty list

    kwargsCMD = {'cwd' : fileDir, 'stdout' : DEVNULL, 'stderr' : STDOUT}        # Set basic keywords for running command
    if kwargs.get('debug', False):                                              # If the debug keyword was set
      kwargsCMD['stdout'] = None                                                # Change stdout so will print for user
      kwargsCMD['stderr'] = None                                                # Change stderr so will pring for user

    self.log.info('Compiling TeX file: {}'.format(infile) )
    cmds = [latex, *bibtex, latex, latex]                                       # List of commands to run

    for i, cmd in enumerate(cmds):                                              # Iterate over list of commands
      proc = self._call( cmd, **kwargsCMD )                                     # Run a command
      if self.BIBTEX[0] not in cmd and proc.returncode != 0:                    # If command does NOT contain bibtex and it did NOT finish cleanly
        self.log.error( 'There was an error compiling: {}'.format(cmd) )        # Log error
        return False                                                            # Return from method
      elif (i == 0):                                                            # Else, if is the first command run
        if auxCheck(*auxFiles, oldData=oldData) is True:                        # Check the aux file data for changes; note that will return False if no aux files existed at begining of compile
          self.log.debug('Aux file(s) unchanged, no need for long compile')     # Log
          break                                                                 # Break from loop as no need to keep compiling; not much changed
        elif len(cmds) == 3:                                                    # Else, if only 3 commands in cmd list, then there were no aux files at start of compile
          auxFiles = self.findAuxFiles()                                        # Find aux files
          for bib in self._bibtex(auxFiles):                                    # Generate bibtex commands and iterate over them
            proc = self._call( bib, **kwargsCMD )                               # Run bibtex command

    if kwargs.get('with_bbl', False):                                           # If the with_bbl keyword is set
      self._insertBib()                                                         # Insert contents of bbl file into the document

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

    fid = tempfile.NamedTemporaryFile( mode='w', suffix='.tex', delete=False )
    fid.write( text )
    fid.close()

    tmpFile = fid.name

    kwargs['srcfmt'] = 'markdown'
    pandoc = self._pandoc(outFile=outFile, **kwargs) 
    try:
      #p1 = Popen( ['echo', text], stdout=PIPE)
      #p2 = Popen( pandoc, cwd = os.path.dirname(outFile), stdin=p1.stdout)
      pandoc.append(tmpFile)
      p2 = Popen( pandoc, cwd = os.path.dirname(outFile) )
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

    fid = tempfile.NamedTemporaryFile( mode='w', suffix='.tex', delete=False )
    fid.write( text )
    fid.close()

    tmpFile = fid.name

    outFile = kwargs.pop('outFile', None)
    kwargs['destfmt'] = 'markdown'
    pandoc = self._pandoc(**kwargs)
    try:
      pandoc.append( tmpFile )
      p2 = Popen( pandoc, cwd = fileDir, stdout=PIPE)
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
      tmp = LaTeX( self.infile, gitBranch = gitBranch )
      fid = tempfile.NamedTemporaryFile( mode='w', suffix='.tex', delete=False )
      fid.write( tmp._text )
      fid.close()

      refFile = fid.name
    elif not refFile:
      return False
 
    self.log.info('Runing latexdiff')
    diff = '{}_track_changes{}'.format( *os.path.splitext(self.infile) )

    fid = tempfile.NamedTemporaryFile( mode='w', suffix='.tex', delete=False )
    fid.write( self._text )
    fid.close()
    newFile = fid.name
    with open(diff, 'w') as fid:
      #proc = Popen( self.LATEXDIFF + [refFile, self.infile], stdout = fid )
      proc = Popen( self.LATEXDIFF + [refFile, newFile], stdout = fid )
      proc.wait()

    if gitBranch:
      self.log.debug('Removing temporary file: {}'.format(refFile) )
      os.remove( refFile )
      os.remove( newFile )

    if proc.returncode == 0:
      return diff
    else:
      self.log.error('There was an error running latexdiff')
      return False
