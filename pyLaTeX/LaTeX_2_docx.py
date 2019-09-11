import os, subprocess;
from LaTeX_crossref import LaTeX_crossref;
from getBibFile import getBibFile;
from replaceAcro import replaceAcro;

def LaTeX_2_docx( file, debug = False ):
    filedir = os.path.dirname( os.path.abspath(file) );
    docx    = '.'.join( file.split('.')[:-1] ) + '.docx'
    lines   = LaTeX_crossref( file, returnLines = True );
    bibFile = getBibFile( lines = lines );
    acroSub = replaceAcro( lines = lines );
    if acroSub.subAcros():
      lines = acroSub.lines;
    if debug:   
        with open(file + '.txt', 'w') as f:
            for line in lines:
                f.write( line );
    base  = ['pandoc', '-f', 'latex', '-t', 'docx']
    opts  = ['--bibliography', bibFile] if bibFile is not None else [];
    files = ['-o', docx]

    try:
        p1 = subprocess.Popen( ['echo', ''.join(lines)], stdout=subprocess.PIPE);
        p2 = subprocess.Popen( base + opts + files, cwd = filedir, stdin=p1.stdout);
        p1.stdout.close();
        p2.communicate();
        code = p2.returncode;
    except:
        print('Pandoc command NOT found!!!');
        code = 127;
    return code;
