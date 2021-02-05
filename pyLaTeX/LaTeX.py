import logging
import os, re
import tempfile
from subprocess import Popen, PIPE, STDOUT, DEVNULL

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
  TEXOPTS   = ['-interaction=nonstopmode'] 

  @property
  def PDFLATEX(self):
    return [ os.path.join( self.texpath, 'pdflatex' ) ]
  @property
  def XELATEX(self):
    return [ os.path.join( self.texpath, 'xelatex' ) ]
  @property
  def BIBTEX(self):
    return [ os.path.join( self.texpath, 'bibtex') ]

  def _bibtex(self, auxFiles):
    """Generate list of bibtex commands to run for each aux file"""

    return [self.BIBTEX + [os.path.basename(aux)] for aux in auxFiles]        # Set bibtex command

  def _call(self, cmd, wait = True, **kwargs):
    """
    Run a given command using subprocess.Popen

    Arguments:
      cmd (list,tuple): Command to run

    Keyword arguments:
      wait (bool): Set to wait for subprocess to finish. Default is to wait.
      **kwargs : Any keywords accepted by subprocess.Popen

    Returns:
      subprocess.Popen instance

    """

    self.log.debug('Running command: {}'.format( cmd ))
    proc = Popen( cmd, **kwargs )
    if wait: proc.wait()
    return proc

  def _checkTeXFile(self, texfile):
    """
    Check texfile input 

    Arguments:
      texfile (str): Path to tex file to process      

    Keyword arguments:
      wait (bool): Set to wait for subprocess to finish. Default is to wait.
      **kwargs : Any keywords accepted by subprocess.Popen

    Returns:
      subprocess.Popen instance

    """
    if texfile is None:                                                         # If texfile is None
      if self.texfile is None:                                                  # If self.texfile is None
        raise Exception('No TeX file specified!')                               # Log error
      return self.texfile                                                       # Set texfile to self.texfile
    return texfile                                                              # Return False

  def findAuxFiles(self, texfile):
    """
    Recursively locate all aux files starting in self.texfile directory

    Arguments:
      texfile (str): Full path of TeX file to be compiled

    Keyword arguments:
      None

    Returns:
      list : Path(s) to aux files

    """

    aux = []                                                                    # List for aux file paths
    for root, dirs, items in os.walk( os.path.dirname( texfile ) ):             # Walk through the directory
      for item in items:                                                        # Iterate over items
        if item.endswith('.aux'):                                               # If file ends with aux
          aux.append( os.path.join( root, item ) )                              # Build file path and append to aux list
    self.log.debug( f'Aux file(s): {aux}' )
    return aux                                                                  # Return list of aux files

  def compile(self, texfile = None, **kwargs):
    """
    Run commands to compile the LaTeX document

    Arguments:
      None.

    Keyword arguments:
      texfile (str): Path to file to convert; not required if a file was
        specified when the class was initialized
      texlive (str): TeXLive version to use to compile
      **kwargs: 
    
    Returns:
      bool : True if compile success, False otherwise

    """

    texfile = self._checkTeXFile( texfile )

    fileDir, fileBase = os.path.split( texfile )                                # Get texfile directory
    auxFiles = self.findAuxFiles( texfile )
    oldData  = auxCheck( *auxFiles )

    if kwargs.get('xelatex', False):                                            # If the xelatex keyword is set
      latex = self.XELATEX                                                      # Use xelatex
    elif re.search('{fontspec}|{mathspec}', self._text) is not None:            # Else, if {fontspec} or {mathspec} found in text
      latex = self.XELATEX                                                      # Use xelatex
    else:                                                                       # Else
      latex = self.PDFLATEX                                                     # Use pdflatex
    latex += self.TEXOPTS + [fileBase]                                          # Append options and file name

    bibtex = self._bibtex( auxFiles )                                           # Set bibtex command; if there were no aux files found, this will be empty list

    kwargsCMD = {'cwd' : fileDir, 'stdout' : DEVNULL, 'stderr' : STDOUT}        # Set basic keywords for running command
    if kwargs.get('debug', False):                                              # If the debug keyword was set
      kwargsCMD['stdout'] = None                                                # Change stdout so will print for user
      kwargsCMD['stderr'] = None                                                # Change stderr so will pring for user

    self.log.info( f'Compiling TeX file: {texfile}' )
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
          auxFiles = self.findAuxFiles( texfile )                               # Find aux files
          for bib in self._bibtex(auxFiles):                                    # Generate bibtex commands and iterate over them
            proc = self._call( bib, **kwargsCMD )                               # Run bibtex command

    if kwargs.get('with_bbl', False):                                           # If the with_bbl keyword is set
      self._insertBib()                                                         # Insert contents of bbl file into the document

  def trackChanges(self, texfile = None, **kwargs): 
    """
    Create tracked changes using the latexdiff CLI

    Arguments:
      None.

    Keyword arguments:
      texfile (str): Path to file to convert; not required if a file was
        specified when the class was initialized
      getBranch  : Git branch where old, reference version is saved
      refFile  : Full path to old, reference file.

    Returns:
      None: but a tracked changes file will be created

    """

    texfile = self._checkTeXFile( texfile )
    diff = self._latexDiff( **kwargs )
    if diff:
      self.compile( texfile = diff, **kwargs)

  def exportTo(self, **kwargs):
    fname, ext = os.path.splitext( self.texfile )																# Get extensionless file path
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
    fileDir = os.path.dirname( self.texfile );
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
      tmp = LaTeX( self.texfile, gitBranch = gitBranch )
      fid = tempfile.NamedTemporaryFile( mode='w', suffix='.tex', delete=False )
      fid.write( tmp._text )
      fid.close()

      refFile = fid.name
    elif not refFile:
      return False
 
    self.log.info('Runing latexdiff')
    diff = '{}_track_changes{}'.format( *os.path.splitext(self.texfile) )

    fid = tempfile.NamedTemporaryFile( mode='w', suffix='.tex', delete=False )
    fid.write( self._text )
    fid.close()
    newFile = fid.name
    with open(diff, 'w') as fid:
      #proc = Popen( self.LATEXDIFF + [refFile, self.texfile], stdout = fid )
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
