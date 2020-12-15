import logging
import os, re, regex
from subprocess import Popen, DEVNULL, STDOUT, PIPE

INPUT     = regex.compile( r'((?:\\input|\\include){([^\}]+)})' )
COMMENT   = regex.compile( r'(?<!\\)(%[^\n\r]*)' )	# Grab instance of % and all following characters IF the % is NOT preceded by \ (backslash)
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

def replaceInputs( texFile, text = None, gitBranch = None ):
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
    gitBranch : The git branch name to pull include/input files from
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
      if gitBranch is None:
        with open(path, 'r') as fid:
          rText = fid.read()
      else:
        rText = gitShow( gitBranch, path )
      text = text.replace( inst[0], rText ) 
  return text 

def gitShow( gitBranch, infile ):
  log  = logging.getLogger(__name__)
  log.info('Getting {} from git branch {}'.format(infile, gitBranch))
  base = os.path.basename(infile)
  proc = Popen( ['git', 'show', '{}:./{}'.format(gitBranch, base)], 
           cwd = os.path.dirname(infile), stdout = PIPE)

  txt = proc.stdout.read().decode()

  proc.wait()

  return removeComments( txt ) 

