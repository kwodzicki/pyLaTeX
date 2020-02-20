import logging
import os, re, regex
from subprocess import Popen, DEVNULL, STDOUT

INPUT     = regex.compile( r'((?:\\input|\\include){(\w+)})' )
COMMENT   = regex.compile( r'(?<!\\)(%.*[\n\r]*)' )	# Grab instance of % and all following characters IF the % is NOT preceded by \ (backslash)
ENVIRON   = r'\\begin{{{}}}((?:(?!\\end{{{}}}).|\n|\r)*)'
RECURSIVE = r'{}({}(?>[^{}{}]|(?{}))*{})' 

def recursiveRegex( qualifier, delimiters, group = 1 ):
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
  fmt = "{}({}(?>[^{}{}]|(?{}))*{})" 
  fmt = fmt.format(qualifier, delimiters[0], *delimiters, group, delimiters[1] )
  return regex.compile( fmt )

def getEnvironment( environ ):
  fmt = ENVIRON.format( environ, environ )
  try:
    return regex.compile( fmt )
  except:
    return re.compile( fmt )

def removeComments( text ):
  '''
  Inputs:
    text   : String of all text in document
  '''
  return COMMENT.sub( '', text )

def replaceInputs( texFile, text = None ):
  '''
  Name:
    replaceInputs:
  Purpose:
    A function to replace any \input{} commands with the
    text from the inputed file
  Inputs:
    texFile  : Full path to tex file
    text     : text from the tex file
  Keywords:
    None.
  Returns:
    Updated text
  '''
  cwd   = os.path.dirname( texFile )
  if not text:
    with open( texFile, 'r' ) as fid:
      text = fid.read()

  insts = INPUT.findall(text)
  for inst in insts:
    dirPath, filePath = os.path.split( inst[1] )
    if not os.path.isabs( dirPath ):
      dirPath = os.path.join( cwd, dirPath )
    if not filePath.endswith('.tex'):
      filePath += '.tex'
    path = os.path.join( dirPath, filePath )
    if os.path.isfile( path ):
      with open(path, 'r') as fid:
        rText = fid.read()
      text = text.replace( inst[0], rText ) 
  return text 

def getBibFile( lines = None, file = None ):
  bibFile = None;                                                               # Initialize bibFile to None
  if lines is None:                                                             # If lines is None
    if file is not None:                                                        # If file is not None
      with open(file, 'r') as f: lines = f.read()                               # Read in all the lines from the file
    else:                                                                       # Else, file is None AND lines is None
      return bibFile;                                                           # Return bibFile, which is None at this point
  elif isinstance(lines, str):
    lines = lines.splitlines()

  if isinstance(lines, list): lines = ''.join(lines)
  res = recursiveRegex( r"\\bibliography", ("{", "}",) ).findall(lines)
  if len(res) == 1:
    bibFile = os.path.expandvars( res[0][1:-1] )                                # Convert bib from list to string and expand all path variables
    if not bibFile.endswith('.bib'): bibFile += '.bib';                         # If the file path does NOT end with .bib, then append .bib
  
  return bibFile


def getAbstract( lines ):
  if isinstance( lines, list): lines = ''.join(lines)
  pattern  = recursiveRegex( r'\\abstract', ('{','}',) )
  abstract = absPat.findall( lines )
  if (len(abstract) == 1):
    return abstract[0][1:-1].splitlines()
  else:
    return None

