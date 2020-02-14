import logging
import os

from .utils import recursiveRegex

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
      self._text = fid.read()
    return True

  def getAbstract(self, text = None):
    if text is None: text = self._text
    res = recursiveRegex(r'\\abstract', ('{','}',)).findall( text )
    if (len(res) == 1):
      return res[0][1:-1].splitlines()
    return None

  def _getBibFile(self):
    res = recursiveRegex( r"\\bibliography", ("{", "}",) ).findall(self._text)
    if len(res) == 1:
      bibFile = os.path.expandvars( res[0][1:-1] )                                # Convert bib from list to string
      if not bibFile.endswith('.bib'): bibFile += '.bib';                         # If the file path does NOT end wi
      return bibFile
    return None

  def _pandoc(self, outFile):
    cmd     = ['pandoc', '-f', 'latex', '-t', 'docx']
    bibFile = self._getBibFile() 
    if bibFile: cmd += ['--bibliography', bibFile]
    return cmd + ['-o', outFile]
