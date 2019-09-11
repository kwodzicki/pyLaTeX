#!/usr/bin/env python3
import os, re;

acroDef = r"\\DeclareAcronym\{([^}]+)\}";      # regex for finding acronym definitions
cmntSub = r"\%(?!\\).*";                       # regex for finding comments
acSubs  = [ (r"\\ac\{([^}]+)\}",  '{}  ({})',  '{}', ), 
            (r"\\acp\{([^}]+)\}", '{}s ({}s)', '{}s', ) ];                      # First part of tuple is regex, second is formatter for acro definition, last is formatter for short form
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
          self.acro[ ac ]['n'] += 1;                                            # Increment the acronym use counter by one (1)
          if self.acro[ ac ]['n'] == 1:                                         # If this is the first time acronym is used
            sub = acSub[1].format(self.acro[ac]['long'],self.acro[ac]['short']);# Set up replacement with long and short forms
          else:                                                                 # Else, is not first time
            sub = acSub[2].format(self.acro[ac]['short']);                      # Set up replacement string
          self.lines[i] = re.sub( 
            acSub[0], lambda _: sub, self.lines[i], count=1
          );                                                                    # Replace first instance in string; return of lambda function is treated as literal string
          tmp = re.search(acSub[0], self.lines[i]);                             # Search for another substitution candidate
    return any( [self.acro[ac]['n'] > 0 for ac in self.acro] );                 # Return True if there was at least one (1) replacement
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
      acro, n = {}, 0;
      while n < self.nLines:                                          # Iterate over all lines
        if 'DeclareAcronym' in self.lines[n]:                         # If acronym declaration is in the line
          line  = self.lines[n];                                      # Set line to the nth line
          nOpen = line.count('{') - line.count('}');                  # Get number of open brackets in the line
          while nOpen > 0:
            n += 1;
            line  += self.lines[n]
            nOpen = line.count('{') - line.count('}');                # Get number of open brackets in the line
          line = re.sub( cmntSub, '',line );                          # Replace any comments in line with empty string
          line = line.replace('\t','');                               # Replace any tabs with empty strings
          tag, line = parseLine( line );
          tmp1 = {'n' : 0}
          for i in line.split(','):
            tmp2 = i.split('=');
            tmp1[tmp2[0].strip()] = tmp2[1].strip();
          acro[tag] = tmp1
        n += 1;
      return acro;


if __name__ == "__main__":
  import sys
  inst = replaceAcro( sys.argv[1] );
  inst.subAcros()
  inst.save();