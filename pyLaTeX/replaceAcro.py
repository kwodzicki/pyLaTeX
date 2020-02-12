import logging
import os
import regex as re

from .utils import recursiveRegex
'''
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
'''
ACRODEF  = recursiveRegex( r'\\DeclareAcronym{([^}]*)}', ('{', '}',), group=2 )
cmntSub = r"\%(?!\\).*";                       # regex for finding comments
acSubs  = [ (r"\\ac{([^}]+)}",  '{}  ({})',  '{}', ), 
            (r"\\acp{([^}]+)}", '{}s ({}s)', '{}s', ) ];                      # First part of tuple is regex, second is formatter for acro definition, last is formatter for short form

class Acronym(object):
  def __init__(self, key, info):
    self.used  = 0
    self._data = {'key' : key}
    for line in info[1:-1].replace(',','').splitlines():
      try:
        key, val = line.split('=')
      except:
        pass
      else:
        self._data[key.strip()] = val.strip()

  def __getitem__(self, key):
    return self._data.get(key, None)
  def __setitem__(self, key, val):
    self._data[key] = val
  def __getattr__(self, key):
    return self._data.get(key, None)
  def __contains__(self, key):
    return key in self._data

def parseLine( line ):
  '''
  Purpose:
    Function for getting acronym tag and 
    definitions from a string
  '''
  tag     = re.findall(acroDef, line)[0];                                       # Pull out the tag
  line    = re.sub(acroDef, '', line);                                          # Replace the tag text with empty string
  n       = 0;                                                                  # Coutner initialized at zero (0)
  newline = '';                                                                 # New line string
  for char in line:                                                             # Iterate over all characters in the line
    if char == '{':                                                             # If the character is open bracket
      n += 1;                                                                   # Increment i
      if n > 1: newline += char;                                                # If i is greater than one (1), then append character to newline
    elif char == '}':                                                           # Else, if character is closed bracket
      n -= 1;                                                                   # Decrement i
      if n > 0: newline += char;                                                # If n is greater than zero (0), then append character to newline
    else:                                                                       # Else, character is not bracket
      newline += char;                                                          # Append character to newline
  return tag, newline                                                           # Return tag and newline

class replaceAcro( object ):
  def __init__(self, infile = None, lines = None):
    if lines is None:
      self.infile = infile
      with open(self.infile, 'r') as f:
        self.lines = f.readlines();
    else:
      self.lines = lines;
    self.nLines = len(self.lines);
    self.acro   = self.parseAcros();
  #########################################
  def save(self):
    outfile  = '.'.join( self.infile.split('.')[:-1] );
    outfile += '_NoACRO.tex';
    if not os.path.isfile( outfile ):
      with open(outfile, 'w') as fid:
        for line in self.lines:
          fid.write( line );
    return outfile;

  #########################################
  def subAcros(self):
    if self.acro is None: return None;                                          # If the acro attribute is None, just return
    document = False;                                                           # Check for document actually started; i.e., past preamble
    for i in range( self.nLines ):                                              # Iterate over all lines
      if not document:                                                          # If document variable is False
        if 'begin{document}' in self.lines[i]:                                  # If check string in line
          document = True;                                                      # Set document to True
        else:                                                                   # Else
          continue;                                                             # Go to next line
      for acSub in acSubs:                                                      # Iterate over all possible substitution types
        tmp = re.search( acSub[0], self.lines[i] );                             # Search for first instance of substitution type
        while tmp is not None:                                                  # While there is a substitution candidate found
          ac = tmp.groups()[0];                                                 # Get text within the {}
          self.acro[ ac ].used += 1;                                            # Increment the acronym use counter by one (1)
          if self.acro[ ac ].used == 1:                                         # If this is the first time acronym is used
            sub = acSub[1].format(self.acro[ac]['long'],self.acro[ac]['short']);# Set up replacement with long and short forms
          else:                                                                 # Else, is not first time
            sub = acSub[2].format(self.acro[ac]['short']);                      # Set up replacement string
          self.lines[i] = re.sub( 
            acSub[0], lambda _: sub, self.lines[i], count=1
          )                                                                     # Replace first instance in string; return of lambda function is treated as literal string
          tmp = re.search(acSub[0], self.lines[i]);                             # Search for another substitution candidate
    return any( [self.acro[ac].used > 0 for ac in self.acro] );                 # Return True if there was at least one (1) replacement

  #########################################
  def parseAcros(self):
    acro = False;
    for line in self.lines:
      if 'usepackage' and 'acro' in line:
        acro = True;
        break;
    if not acro:
      return None;
    else:
      acronyms = {}
      for match in ACRODEF.findall( ''.join(self.lines) ):
        acro = Acronym( *match )
        if 'key' in acro:
          acronyms[ acro['key'] ] = acro
      return acronyms
