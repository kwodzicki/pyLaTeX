#!/usr/bin/env python3
# A function to parse a LaTeX document and get the path to the
# bibliography file, if any.

import os, re;
def getBibFile( lines = None, file = None ):
	bibFile = None;                                                               # Initialize bibFile to None
	if lines is None:                                                             # If lines is None
		if file is not None:                                                        # If file is not None
			with open(file, 'r') as f: lines = f.readlines();                         # Read in all the lines from the file
		else:                                                                       # Else, file is None AND lines is None
			return bibFile;                                                           # Return bibFile, which is None at this point
	for line in lines:                                                            # Iterate over every line in lines
		if '\\bibliography{' in line and '%' not in line:                           # If the \bibliography{} command is in the line and there is no comment character (%)
			bibFile = re.findall(r"\\bibliography\{([^}]+)\}", line);                 # Get the information in the \bibliography command
			if len(bibFile) == 1:                                                     # If the length of bibFile is one (1)
				bibFile = os.path.expandvars( bibFile[0] );                             # Convert bib from list to string and expand all path variables
				if not bibFile.endswith('.bib'): bibFile += '.bib';                     # If the file path does NOT end with .bib, then append .bib
				break;                                                                  # Break the for loop over lines
	return bibFile;                                                               # Return the bibFile path