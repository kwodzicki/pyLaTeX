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

ACRODEF  = recursiveRegex( r'\\DeclareAcronym{([^}]*)}', ('{', '}',), group=2 )
cmntSub = r"\%(?!\\).*";                       # regex for finding comments
acSubs  = [ (r"\\ac{([^}]+)}",  '{}  ({})',  '{}', ), 
            (r"\\acp{([^}]+)}", '{}s ({}s)', '{}s', ) ];                      # First part of tuple is regex, second is formatter for acro definition, last is formatter for short form

class Acronyms( LaTeXBase ):
  def __init__(self, *args, **kwargs):
    acros = kwargs.pop('acros', None)
    super().__init__(*args, **kwargs)
    self.acro = self._parseAcros( acros )

  #########################################
  def save(self):
    outfile  = '.'.join( self.texfile.split('.')[:-1] );
    outfile += '_NoACRO.tex';
    if not os.path.isfile( outfile ):
      with open(outfile, 'w') as fid:
        fid.write( self._text )
    return outfile;

  #########################################
  def subAcros(self, text = None):
    if self.acro is None: return None;                                          # If the acro attribute is None, just return
    document = False;                                                           # Check for document actually started; i.e., past preamble
    if text is None:
      lines = self._text.splitlines(True)
    else:
      lines = text.splitlines(True)

    for i, line in enumerate(lines):                                            # Iterate over all lines
      if not document:                                                          # If document variable is False
        if 'begin{document}' in line:																						# If check string in line
          document = True;                                                      # Set document to True
        else:                                                                   # Else
          continue;                                                             # Go to next line
      for acSub in acSubs:                                                      # Iterate over all possible substitution types
        tmp = re.search( acSub[0], line )																				# Search for first instance of substitution type
        while tmp is not None:                                                  # While there is a substitution candidate found
          ac = tmp.groups()[0]																									# Get text within the {}
          self.acro[ ac ]['used'] += 1																					# Increment the acronym use counter by one (1)
          if self.acro[ ac ]['used'] == 1:                                      # If this is the first time acronym is used
            sub = acSub[1].format(self.acro[ac]['long'],self.acro[ac]['short'])	# Set up replacement with long and short forms
          else:                                                                 # Else, is not first time
            sub = acSub[2].format(self.acro[ac]['short'])												# Set up replacement string
          line = re.sub( acSub[0], lambda _: sub, line, count=1)                # Replace first instance in string; return of lambda function is treated as literal string
          tmp = re.search(acSub[0], line);																			# Search for another substitution candidate
      lines[i] = line
    text = ''.join(lines)
    return text

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
