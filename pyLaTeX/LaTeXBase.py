import logging
import os, re

from . import VERSIONS
from .utils import recursiveRegex, replaceInputs, removeComments, gitShow

TEXROOT_PATTERN = re.compile( r"\!TEX root\s*=\s*(.*)" )

class LaTeXBase( object ):
  def __init__(self, texfile, gitBranch=None, texlive='Latest'):
    self._texlive  = 'Latest'
    self._texfile  = None
    self._text     = None

    self.log       = logging.getLogger(__name__)
    self.gitBranch = gitBranch
    self.texlive   = texlive
    self.loadFile( texfile )
   
  @property
  def texfile(self):
    return self._texfile
  @texfile.setter
  def texfile(self, val):
    if not val:
      raise Exception('Input file not defined')
    elif not os.path.isfile( val ):
      raise Exception('File does not exist')
    elif not val.endswith('.tex'):
      raise Exception('Invalid file exception')
    self._texfile = os.path.abspath( val ) 

  @property
  def texlive(self):
    return self._texlive
  @texlive.setter
  def texlive(self, val):
    if isinstance(val, str) and val in VERSIONS:
      self._texlive = val
    elif val is not None:
      self.log.error( f'Not a valid texlive version: {val}' )

  @property
  def texpath(self):
    return VERSIONS[ self._texlive ] 
  def loadFile(self, texfile):
    self.texfile = texfile
    text = self._findRoot( )
    self._text = replaceInputs( self.texfile, text, self.gitBranch )

    return True

  def insertAbstract(self, text = None):
    if text is None: text = self._text
    res = recursiveRegex(r'\\abstract', ('{','}',)).findall( text )
    if (len(res) == 1):
      res  = res[0][1:-1]
      sub  = r'\\begin{document}'
      text = re.sub(sub+'[\n\r]', sub+r'\n\\section{Abstract}\n'+res, text)
    return text

  def getTitle(self, text = None):
    if text is None: 
      text = self._text
      #text = removeComments( self._text )
    res = recursiveRegex(r'\\title', ('{','}',)).findall( text )
    if (len(res) == 1):
      return res[0][1:-1]
    return None

  def getAuthors(self, text = None):
    if text is None: 
      text = self._text
      #text = removeComments(self._text)
    res = recursiveRegex(r'\\authors', ('{','}',)).findall( text )
    if (len(res) == 1):
      res = re.sub( r'\\\w+{[^}]+}', '', res[0][1:-1] )
      return '; '.join( [i.strip().rstrip() for i in res.split('and')] )
    return None

  def getBibFile(self, text = None):
    if text is None:
      text = self._text
      #text = removeComments(self._text)
    for tmp in ['bibliography', 'bibFile']:
      res = recursiveRegex( r"\\"+tmp, ("{", "}",) ).findall(text)
      if len(res) == 1:
        bibFile = os.path.expandvars( res[0][1:-1] )                                # Convert bib from list to string
        if not bibFile.endswith('.bib'): bibFile += '.bib';                         # If the file path does NOT end wi
        self.log.debug('Using bib file: {}'.format(bibFile))
        return bibFile
    return None

  def _findRoot(self):
    """
    Determine full path to TeX root file

    Looks for existance of '!TEX root = ...' in the self.texfile
    defined. If the TEX root variable is defined, then that path
    is parsed in attempt to locate root document and the root
    document is compiled.

    Arguments:
      None.

    Keyword arguments:
      None.

    Returns:
      str: Text of the source document
    """

    if self.gitBranch is None:
      with open(self.texfile, 'r') as fid:                                         # Open source file for reading
        text = fid.read()                                                         # Read in all text
    else:
      text = gitShow( self.gitBranch, self.texfile )

    rootFile = TEXROOT_PATTERN.findall( text )                                  # Look for the !TEX root pattern
    if len(rootFile) != 1:
      return removeComments(text)                                               # If no pattern, or more than one patter found; just return the text of the file

    rootFile = rootFile[0]                                                      # Take first instance of !TEX root pattern
    if os.path.relpath( rootFile ):                                             # If it is a relative path
      path = os.path.dirname( self.texfile )                                     # Get directory path of the self.texfile
      path = os.path.join( path, rootFile )                                     # Add the relative root path to the self.texfile directory path
      path = os.path.abspath(path)                                              # Get absolute path
    else:
      path = os.path.abspath(path)                                              # Else, just get absolute path to be sure

    if path == self.texfile:                                                    # If file paths, equal (not likely?) then just return text
      return removeComments(text)                                               # Return text
    else:
      self.log.info( 'Root TeX file found: {}'.format(path) )
      self.texfile = path                                                       # Else, update texfile path
      return self._findRoot()                                                   # Recursive call to this method

  def _insertBib(self):
    """
    Method to insert the contents of a bbl file into TeX source
    
    Takes contents of the bbl file created when running BibTeX and
    creates new TeX file with contents of bbl file located where 
    the \\bibliography{} command existed in the original file.
    
    Note:
      All comments are removed in new file

    Arguments:
      None.

    Keyword arguments:
      None.

    Returns:
      None.  Creates new file though!
    """

    filePath, fileExt = os.path.splitext(self.texfile)														# Split extension off file path
    bblFile = '{}.bbl'.format( filePath )																				# Path to bbl file
    newFile = '{}_wBBL.tex'.format( filePath )																	# Path to new file with bbl replace
    if not os.path.isfile( bblFile ):																						# If NO bbl file
      self.log.error('No bbl file! Cannot replace contents')
    else:
      self.log.debug('Reading bbl data from: {}'.format(bblFile))
      with open(bblFile, 'r') as fid:
        bblData = fid.read()
      bblData = bblData.replace('\\', '\\\\')																		# Replace all \\ with \\\\

      text    = self._text 											# Remove comments from original latex data
      #text    = removeComments( self._text )																		# Remove comments from original latex data
      text    = re.sub( r'\\bibliographystyle{[^}]+}', '',      text )								# Remove nay bibliographystyle commands
      text    = re.sub( r'\\bibliography{[^}]+}',      bblData, text )								# Replace bibliography command with contents of bbl file
      self.log.debug('Creating new file: {}'.format(newFile))
      with open(newFile, 'w') as fid:
        fid.write( text )

  def _pandoc(self, outFile=None, **kwargs):
    cmd     = ['pandoc', '--from', kwargs.get('srcfmt',  'latex'), 
                         '--to',   kwargs.get('destfmt', 'docx')]
    if kwargs.get('bibFile', None):
      cmd += ['--bibliography', kwargs.get('bibFile')]
    cmd.append( '-o' )
    if outFile:
      cmd.append( outFile )
    else:
      cmd.append( '-' )
    self.log.debug( 'Pandoc cmd: {}'.format(cmd))
    return cmd 
