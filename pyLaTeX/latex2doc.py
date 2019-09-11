#!/usr/bin/env python3
# LaTeX to Word

import os
def latex2doc( infile ):
	infile  = os.path.abspath( infile )
	outfile = infile.replace('.tex', '.doc');
	print( outfile );
	docClass = ''
	commands = []
	packages = []
	text     = []
	with open(infile, 'r') as f:
		line = f.readline();
		while 'begin{document}' not in line:
			if 'usepackage' in line:
				packages.extend(line.replace('{',',').replace('}',',').split(',')[1:-1]);
			elif 'newcommand' in line:
				commands.append(line.rstrip);
			line = f.readline();
		while 'end{document}' not in line:
			if line[0] != '%': text.append(line);
			line = f.readline();
	with open(outfile, 'w') as f:
		for line in text:
			f.write( line );



if __name__ == "__main__":
	import sys
	if len(sys.argv) != 2:
		print( 'Incorrect number of inputs' );
		exit(1);
	latex2doc( sys.argv[1] );