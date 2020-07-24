import logging
import os, re

from .utils import recursiveRegex, replaceInputs, removeComments

class LaTeXBase( object ):
  _infile   = None
  _text     = None
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
      text = fid.read()
    self._text = replaceInputs( infile, text )
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
      text = removeComments( self._text )
    res = recursiveRegex(r'\\title', ('{','}',)).findall( text )
    if (len(res) == 1):
      return res[0][1:-1]
    return None

  def getAuthors(self, text = None):
    if text is None: 
      text = removeComments(self._text)
    res = recursiveRegex(r'\\authors', ('{','}',)).findall( text )
    if (len(res) == 1):
      res = re.sub( r'\\\w+{[^}]+}', '', res[0][1:-1] )
      return '; '.join( [i.strip().rstrip() for i in res.split('and')] )
    return None

  def getBibFile(self, text = None):
    if text is None:
      text = removeComments(self._text)
    res = recursiveRegex( r"\\bibliography", ("{", "}",) ).findall(text)
    if len(res) == 1:
      bibFile = os.path.expandvars( res[0][1:-1] )                                # Convert bib from list to string
      if not bibFile.endswith('.bib'): bibFile += '.bib';                         # If the file path does NOT end wi
      return bibFile
    return None

  def _insertBib(self):
    '''
    Purpose:
      Method to insert the contents of a bbl file into TeX
      where \\bibliography{} command exists, creating
      new file with data. Note that all comments are removed
      in new file
    Inputs:
      None.
    Keywords:
      None.
    Outputs:
      None.  Creates new file though!
    '''
    filePath, fileExt = os.path.splitext(self.infile)														# Split extension off file path
    bblFile = '{}.bbl'.format( filePath )																				# Path to bbl file
    newFile = '{}_wBBL.tex'.format( filePath )																	# Path to new file with bbl replace
    if not os.path.isfile( bblFile ):																						# If NO bbl file
      self.log.error('No bbl file! Cannot replace contents')
    else:
      self.log.debug('Reading bbl data from: {}'.format(bblFile))
      with open(bblFile, 'r') as fid:
        bblData = fid.read()
      bblData = bblData.replace('\\', '\\\\')																		# Replace all \\ with \\\\

      text    = removeComments( self._text )																		# Remove comments from original latex data
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
