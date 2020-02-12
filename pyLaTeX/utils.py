import logging
import os, regex
from subprocess import Popen, DEVNULL, STDOUT

def recursiveRegex( qualifier, delimiters ):
  '''
  Purpose:
    To create a regex pattern for extracting information
  Inputs:
    qualifier   : Qualifying text, such as bibliography
    delimieters : Tuple with starting/ending delimiters, such as ('{','}')
  Keywords:
    None.
  Returns:
    Returns regex pattern
  Notes about regex pattern:
    See link for examples  
      https://www.regular-expressions.info/refrecurse.html
    In words:
      Recurusion of a capturing group
      Find the qualifier string (case-sensitive)
      Then use the basic pattern b(?>m|(?R))e where b is
      matching construct, m is what can occur in middle, and e is ending.
      In this case, m is[^{}], i.e., not one of those characters,
      or the matching construct. To get around the case where b
      is all the text preceding the parenthesis, we replace (?R)
      with (?1), a reference to the first caputure group. This
      is all placed inside a capture group.

      Note that this capture group will contain the opening and
      closing {}, so best to do match[1:-1] to get rid of them
  '''
  fmt = "{}({}(?>[^{}{}]|(?1))*{})" 
  fmt = fmt.format(qualifier, delimiters[0], *delimiters, delimiters[1] )
  return regex.compile( fmt )


def build(inFile, **kwargs):
  log      = logging.getLogger(__name__)
  buildDir = os.path.dirname(inFile)
  auxFile  = os.path.splitext(inFile)[0] + '.aux'
  LaTeXCMD = 'xelatex' if kwargs.get('xelatex', False) else 'pdflatex'
  LaTeXCMD = [LaTeXCMD, '-interaction=nonstopmode', os.path.basename( inFile )]
  bibTex   = ['bibtex',   os.path.basename( auxFile )]

  kwargsCMD = {'cwd'    : buildDir,
               'stdout' : DEVNULL,
               'stderr' : STDOUT}
  if kwargs.get('debug', False):
    kwargsCMD['stdout'] = None
    kwargsCMD['stderr'] = None

  log.info( 'Compiling TeX file: {}'.format( inFile ) )
  cmds     = [LaTeXCMD, bibTex, LaTeXCMD, LaTeXCMD]
  for cmd in cmds:
    proc = Popen( cmd, **kwargsCMD )
    proc.wait()

def getBibFile( lines = None, file = None ):
  bibFile = None;                                                               # Initialize bibFile to None
  if lines is None:                                                             # If lines is None
    if file is not None:                                                        # If file is not None
      with open(file, 'r') as f: lines = f.read()                               # Read in all the lines from the file
    else:                                                                       # Else, file is None AND lines is None
      return bibFile;                                                           # Return bibFile, which is None at this point
  if isinstance(lines, list): lines = ''.join(lines)
  res = recursiveRegex( r"\\bibliography", ("{", "}",) ).findall(lines)
  if len(res) == 1:
    bibFile = os.path.expandvars( res[0][1:-1] )                                # Convert bib from list to string and expand all path variables
    if not bibFile.endswith('.bib'): bibFile += '.bib';                         # If the file path does NOT end with .bib, then append .bib
  
  return bibFile


