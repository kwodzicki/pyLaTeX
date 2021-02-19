import logging
import os
import regex as re

from .LaTeXBase import LaTeXBase
from .utils import recursiveRegex

"""
The ACRODEF regex pattern was found at the following link:
https://www.regular-expressions.info/refrecurse.html

In words:
    Recurusion of a capturing group
    Find the 'DeclareAcronym' string (case-sensitive)
    Then use the basic pattern b(?>m|(?R))e where b is
    matching construct, m is what can occur in middle, and
    e is ending.
    In this case, m is[^{}], i.e., not one of those characters,
    or the matching construct. To get around the case where b
    is all the text preceding the parenthesis, we replace (?R)
    with (?1), a reference to the first caputure group. This
    is all placed inside a capture group. 

    Note that this capture group will contain the opening and
    closing {}, so best to do match[1:-1] to get rid of them
"""

ACRODEF = recursiveRegex( r'\\DeclareAcronym{([^}]*)}', ('{', '}',), group=2 )
ACSUBS  = {
        r"\\ac{([^}]+)}" : {
            'unused' : {
                'keys'   : ('long', 'short',),
                'format' : '{}  ({})'},
            'used'   : {
                'keys'   : ('short',),
                'format' :'{}'},
            },
        r"\\acp{([^}]+)}" : {
            'unused' : {
                'keys'   : ('long', 'short',),
                'format' : '{}s ({}s)'},
            'used'   : {
                'keys'   : ('short',),
                'format' : '{}s'},
            },
        r"\\acs{([^}]+)}" : {
            'keys'   : ('short',),
            'format' : '{}'},
        r"\\acl{([^}]+)}" : {
            'keys'   : ('long',),
            'format' : '{}'},
         }

class Acronyms( LaTeXBase ):
  def __init__(self, *args, **kwargs):
    acros = kwargs.pop('acros', None)
    super().__init__(*args, **kwargs)
    self.acro = self._parseAcros( acros )

  #########################################
  def save(self, **kwargs):
    outfile, ext  = os.path.splitext( self.texfile )
    outfile      += '_NoACRO.tex'
    with open(outfile, 'w') as fid:
      fid.write( self.subAcros( **kwargs ) )
    return outfile

  #########################################
  def subAcros(self, text = None, **kwargs):
    """
    Substitute all acronym calls in text

    All (well, most) acronym calls in text will be subsitituded
    for their full (or short) version.

    Arguments:
      None.

    Keyword arguments:
      text (str) : Text to substitude acronyms in.
        Default is text read in from supplied TeX file
      **kwargs : Silently ignores other keywords

    Returns:
      str : Text with acro calls replaced

    """

    if self.acro is None: return None                                           # If the acro attribute is None, just return
    if text is None:
      lines = self._text.splitlines(True)
    else:
      lines = text.splitlines(True)

    document = False                                                            # Check for document actually started; i.e., past preamble
    for i, line in enumerate(lines):                                            # Iterate over all lines
      if not document:                                                          # If document variable is False
        if 'begin{document}' in line:					        # If check string in line
          document = True                                                       # Set document to True
        else:                                                                   # Else
          continue                                                              # Go to next line
      elif '\\acreset' in line:                                                 # If acreset is in line; this handles specific resets as well as the acresetall command
        tmp = re.search( r"\\acreset{([^}]+)}", line )				# Search for first instance of specific resets
        if tmp:                                                                 # If any found
          for ac in tmp.groups()[0].split(','):					# Iterate over all acronyms to reset
            self.acro[ac]['used'] = 0                                           # Reset usage state
        else:                                                                   # Else, assume resetting all
          for ac in self.acro:					                # Iterate over all defined acronyms
            self.acro[ac]['used'] = 0                                           # Set used state to zero
        lines[i] = ''                                                           # Remove the command from the line
      else:
        lines[i] = self._lineSub( line )
    text = ''.join(lines)
    return text

  def _lineSub(self, line):
    """
    Substitute all acro commands in a given line

    The various regex subsitition keys in the ACSUBS dict are tested
    on the input line. As any one subsitition may, itself, include an
    acronym definitions, a main while loop is used to check for the
    occurence of any of the regex patterns in the line. While any
    patterns exists, will keep rechecking the line.

    Arguments:
      line (str) : Line to replace acronym commands in

    Keyword arguments:
      None.

    Returns:
      str : Line with acronym commands replaced

    """

    ff = '|'.join( ACSUBS.keys() )                                              # Regex pattern that looks for all the various subsitutions
    while re.search( ff, line ):
      for acReg, acFMT in ACSUBS.items():                                       # Iterate over all possible substitution types
        tmp = re.search( acReg, line )						# Search for first instance of substitution type
        while tmp is not None:                                                  # While there is a substitution candidate found
          ac = tmp.groups()[0]						        # Get text within the {}
          if 'used' not in acFMT:                                               # If 'used' not in format dictionary
            info = acFMT                                                        # Set info to acFMT
          else:                                                                 # Else, more complex 
            self.acro[ ac ]['used'] += 1					# Increment the acronym use counter by one (1)
            key  = 'unused' if self.acro[ ac ]['used'] == 1 else 'used'         # If this is the first time acronym is used, set key to unused
            info = acFMT[key]                                                   # Set info to sub-dictionary of acFMT

          vals = [ self.acro[ac].get(k, '') for k in info['keys'] ]             # Get all acronym information for replacing call 
          sub  = info['format'].format( *vals )                                 # Generate replacement string
          line = re.sub( acReg, lambda _: sub, line, count=1)                   # Replace first instance in string; return of lambda function is treated as literal string
          tmp  = re.search(acReg, line)					        # Search for another substitution candidate
    return line

  #########################################
  def _parseAcros(self, acroFile=None):
    if acroFile is not None:
      self.log.debug(f'Using acronym definitions from: {acroFile}')
      with open(acroFile, 'r') as fid:
        text = fid.read()
    else:
      acro = False
      for line in self._text.splitlines():
        if 'usepackage' and 'acro' in line:
          acro = True;
          break;
      if not acro:
        return None;
      else:
        text = self._text
    acronyms = {}
    for acro, info in ACRODEF.findall( text ):
      acronyms[acro] = {'used' : 0}
      for keyVal in info[1:-1].replace(',','\n').splitlines():
        try:
          key, val = keyVal.split('=')
        except:
          pass
        else:
          acronyms[acro].update( {key.strip() : val.strip()} )
    return acronyms
