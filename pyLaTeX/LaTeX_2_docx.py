import logging
import os, re
from subprocess import Popen, PIPE
from .LaTeX_crossref import LaTeX_crossref;
from .utils import getBibFile;
from .replaceAcro import replaceAcro;

absPat = re.compile( r'\\abstract\{([^\[\]]+?)\}' )

def getAbstract( lines ):
    abstract = absPat.findall( ''.join(lines) )
    if (len(abstract) == 1):
        return abstract[0].splitlines()
    else:
        return None

def LaTeX_2_docx( file, **kwargs ):
    filedir = os.path.dirname( os.path.abspath(file) );
    fname, ext = os.path.splitext( file )
    docx    = '{}.docx'.format( fname )
    md      = '{}.md'.format(   fname )
    lines   = LaTeX_crossref( file, returnLines = True );
    bibFile = getBibFile( lines = lines );
    acroSub = replaceAcro( lines = lines );
    if acroSub.subAcros():
      lines = acroSub.lines;

    abstract = getAbstract( lines )

    if kwargs.get('debug', False):   
        with open(file + '.txt', 'w') as f:
            for line in lines:
                f.write( line );


#    base  = ['pandoc', '-f', 'latex', '-t', 'markdown']
#    opts  = ['--bibliography', bibFile] if bibFile is not None else [];
#    files = []#'-o', md]

#    try:
#        p1 = Popen( ['echo', ''.join(lines)], stdout=PIPE)
#        p2 = Popen( base + opts + files, cwd = filedir, stdin=p1.stdout, stdout=PIPE)
#        p1.stdout.close();
#        lines = p2.communicate()[0]
#        code = p2.returncode;
#    except:
#        print('Pandoc command NOT found!!!');
#        code = 127;

    base  = ['pandoc', '-f', 'latex', '-t', 'docx']
    opts  = ['--bibliography', bibFile] if bibFile is not None else [];
    files = ['-o', docx]

    try:
        p1 = Popen( ['echo', ''.join(lines)], stdout=PIPE)
        p2 = Popen( base + opts + files, cwd = filedir, stdin=p1.stdout)
        p1.stdout.close()
        p2.communicate()
        code = p2.returncode
    except:
        print('Pandoc command NOT found!!!')
        code = 127
    return code
