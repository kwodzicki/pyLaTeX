#!/usr/bin/env python

import os, re
from pylatexenc.latexencode import unicode_to_latex

nTabs   = 4
tabStop = 4
offset  = nTabs * tabStop

def encodeLaTeX( text ):
    text = unicode_to_latex( text )
    text = text.replace( '\\textquotedblleft',  "``" )
    text = text.replace( '\\textquotedblright', "''" )
    return text

def parseRefType( line ):
    refType = line.split('-')[1].strip().upper()
    if (refType == 'JOUR'):
        return 'article'
    else:
        return None

def parseLine( line ):
    return '-'.join( line.rstrip().split('-')[1:] ).strip()

def ris2bib( file, outfile = None, mode = 'a' ):
    try:
        fid = open(file, 'r')
    except:
        print('Failed to open file')
        return False
    
    data    = {}
    refType = None
    for line in fid.readlines():
        if re.match( r'^TY', line):                 # This is reference type
            refType = parseRefType( line )
            if (refType is None):
                break
        elif re.match( r'(^A\d+)|(^AU)', line):     # Author
            if ('author' in data):
                data['author'].append( parseLine( line ) )
            else:
                data['author'] = [parseLine( line )]
        elif re.match( r'(^PY)', line ):
            data['year'] = parseLine( line )
        elif re.match( r'^TI', line ):              # Title
            data['title'] = parseLine( line )
        elif re.match( r'^JO', line ):
            data['journal'] = parseLine( line )
        elif re.match( r'^SP', line ):
            data['start-page'] = parseLine( line )
        elif re.match( r'^EP', line ):
            data['end-page']   = parseLine( line )
        elif re.match( r'^VL', line ):
            data['volume']    = parseLine( line )
        elif re.match( r'^IS', line ):
            data['number']    = parseLine( line )
        elif re.match( r'^AB', line ):
            data['abstract']  = parseLine( line )
        elif re.match( r'SN', line ):
            data['issn']      = parseLine( line )
        elif re.match( r'^UR', line ):
            data['url']       = parseLine( line )
        elif re.match( r'^DO', line ):
            data['doi']       = parseLine( line )
    
    fid.close()
    if (refType is None):
        return False

    key = data['author'][0].split(',')[0]
    if (len(data['author']) == 2):
        key += '_{}:'.format( data['author'][1].split(',')[0] )
    elif (len(data['author']) > 2):
        key += '_etal:'
    key += data['year']

    if ('start-page' in data) and ('end-page' in data):
        data['pages'] = '{}--{}'.format(data.pop('start-page'), data.pop('end-page'))

    text  = '@{}{}{},\n'.format( refType, '{', key )

    for key, val in data.items():
        nSpace = (offset - tabStop - len(key))
        nTab   = nSpace // tabStop
        if (nSpace % tabStop) != 0:
            nTab += 1

        fmt  = '\t{}'
        for i in range( nTab ): fmt += '\t'
        fmt += '= {{{}}},\n'
        if (key == 'author'):
            text += fmt.format( key, ' and '.join( val ) )
        else:
            text += fmt.format( key, val )
    text = text[:-2] + '\n}\n'
   
    test = encodeLaTeX( text )
 
    if (outfile is None):
        print( text )
    else:
        with open(outfile, mode = mode) as oid:
            oid.write( text )
    return True
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('risfile',      type = str, help='Full path to ris citation file')
    parser.add_argument('-b', '--bib',  type = str, help='Full path to .bib file to append converted citation to')

    args = parser.parse_args()
    ris2bib( args.risfile, outfile = args.bib  )

