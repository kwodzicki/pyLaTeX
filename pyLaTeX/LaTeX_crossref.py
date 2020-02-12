#!/usr/bin/env python3

# A python function to replace figure, table, and equation labels with numbers
import os, re;
caption = re.compile(r"\{(([^\{]|\{\})*)\}")
pattern = re.compile(r"\\label\{([^}]+)\}");

info = {'Figure'   : {'list' : [], 'num' : 1},
        'Table'    : {'list' : [], 'num' : 1},
        'equation' : {'list' : [], 'num' : 1}}

def getContents( str, brackets ):
  nBracket = 0;
  contents = '';
  i = 0
  while i < len(str):
    if str[i] == brackets[0]:
      if (contents != ''):
        if not isinstance(contents, list):
          contents = [contents]
        contents += ['']
      if nBracket == 0: i+=1;
      nBracket += 1;
    elif str[i] == brackets[1]:
      nBracket -= 1;
    if nBracket > 0:
      if isinstance(contents, list):
        contents[-1] += str[i]
      else: 
        contents += str[i]
    i+=1;
  return contents;
  
def replaceLabels( lines ):
  lineNum, nLines = 0, len(lines);
  while lineNum < nLines:                                                       # While the lineNum variable is less than the number of lines, continue processing
    for tag in info:                                                            # Iterate over all tags in the info dictionary
      if '\\begin{'+tag.lower()+'}' in lines[lineNum] and '%' not in lines[lineNum]:# If an environment matching tag is beginning in the line
        while '\\end{'+tag.lower()+'}' not in lines[lineNum]:                   # While the line does NOT contain the end statement for the environment
          lineNum += 1;                                                         # Increase the line number
          if '\\label{' in lines[lineNum]:                                      # If there is a label command in the line
            label = re.findall(r"\\label\{([^}]+)\}", lines[lineNum]);          # Get the label text
            lines[lineNum] = re.sub(pattern, '', lines[lineNum]);               # Replace the label command with nothing
            if len(label) == 1:                                                 # Check that the label variable is only one (1) element
              info[tag]['list'].append( (str(info[tag]['num']), label[0]) );    # Append the object number and label tupel to the list under tag in info
              info[tag]['num'] += 1;                                            # Increase the object number under tag of info by one
    lineNum += 1;                                                               # Increment the line number by one (1)
  for i in range( nLines ):                                                     # Iterate over all lines from file
    for tag in info:                                                            # Iterate over all tags in the info dictionary
      for label in info[tag]['list']:                                           # Iterate over all labels
        if label[1] in lines[i]:                                                # If the label is in the line
          words = lines[i].split();                                             # Split the line on spaces
          for j in range( len(words) ):                                         # Iterate over each word
            if label[1] in words[j]:                                            # If the object label is in the word
              tmp = words[j].split('}');                                        # Split the word on the '}' character
              words[j] = label[0] + (tmp[1] if len(tmp) == 2 else '');          # Append any trailing information to the object number
          lines[i] = ' '.join(words);                                           # Replace the line with the updated list of words
  for tag in info: info[tag]['num'] = 1;                                        # Reset numbers in info to one (1)
  return lines;

def updateCaptions( lines ):
  lineNum, nLines = 0, len(lines);
  while lineNum < nLines:                                                       # While the lineNum variable is less than the number of lines, continue processing
    for tag in info:                                                            # Iterate over all tags in the info dictionary
      if '\\begin{'+tag.lower()+'}' in lines[lineNum] and '%' not in lines[lineNum]:# If an environment matching tag is beginning in the line
        capNum = None;
        while '\\end{'+tag.lower()+'}' not in lines[lineNum]:                   # While the line does NOT contain the end statement for the environment
          lineNum += 1;                                                         # Increase the line number
          if '\\caption{' in lines[lineNum]: capNum = lineNum;                  # If the line contains a caption, save the line number
        if capNum is not None:
          caption       = getContents( '\n'.join( lines[capNum:lineNum] ), ('{', '}') );
          caption       = ''.join(caption)
          caption       = ['{}\n'.format(line) for line in caption.splitlines() if (line != '')]
          caption[0]    = '{} {} {}'.format(tag, info[tag]['num'], caption[0])
          lines[capNum] = '\\caption{' + caption[0]
          if len(caption) == 1:
            lines[capNum] += '}\n'
          else:
            for k in range(1, len(caption)):
              lines[capNum+k] = caption[k]
            lines[capNum+k] += '}\n'
          info[tag]['num'] += 1;                                                # Increase the object number under tag of info by one (1)
          capNum = None;                                                        # Set capNum to None
    lineNum += 1;                                                               # Increment the line number by one (1)
  return lines;

def LaTeX_crossref( file = None, lines = None, returnLines = False ):
  if lines is None:
    if file is None:
      raise Exception('Must input file path or lines')
    else:
      with open(file, 'r') as f: lines = f.readlines();                             # Read all lines in the file
  elif isinstance(lines, str):
    lines = lines.splitlines()
    
  lines = updateCaptions( replaceLabels( lines ) );
  
  if returnLines:                                                               # If returnLines is set
    return lines;                                                               # Return the lines
  else:                                                                         # Else, write lines to output file and return out file path
    out = os.path.abspath(file);
    out = '.'.join( out.split('.')[:-1] ) + '_crossref.tex';
    with open(out, 'w') as f:                                                   # Open the output file for writing
      for line in lines:                                                        # Iterate over all lines in lines variable
        f.write(line);                                                          # Write the line to the file
    return out;                                                                 # Return the new file name
              
if __name__ == "__main__":
  import sys
  if len(sys.argv) != 2:
    print( 'Incorrect number of inputs!' );
    exit(1)
  out = LaTeX_crossref( sys.argv[1] );
