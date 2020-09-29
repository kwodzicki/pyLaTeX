import logging
import os
from subprocess import check_output

log = logging.getLogger(__name__)
log.setLevel( logging.DEBUG )
log.addHandler( logging.StreamHandler() )
log.handlers[0].setFormatter(
  logging.Formatter( '%(asctime)s [%(levelname)-4.4s] %(message)s' )
)


cmd       = check_output(['which', 'pdflatex']).decode().rstrip()
cmd       = os.path.dirname( cmd )

root, sub = cmd.split('Latest')
if sub[0] == os.sep: sub = sub[1:]

vers      = [ver for ver in os.listdir(root) if ver.isdigit()]
dirs      = [os.path.join(root, ver, sub) for ver in vers if ver.isdigit()]

VERSIONS = dict( zip( vers, dirs ) ) 
VERSIONS['Latest'] = cmd

