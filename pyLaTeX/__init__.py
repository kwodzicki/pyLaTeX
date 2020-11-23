import logging
import os
from subprocess import check_output

log = logging.getLogger(__name__)
log.setLevel( logging.DEBUG )
log.addHandler( logging.StreamHandler() )
log.handlers[0].setFormatter(
  logging.Formatter( '%(asctime)s [%(levelname)-4.4s] %(message)s' )
)

latest    = 'Latest'                                                            # Set name for latest directory
cmd       = ['which', 'pdflatex']                                               # Set command to run to find pdflatex
cmd       = check_output( cmd ).decode().rstrip()                               # Run command to find
cmd       = os.path.dirname( cmd )                                              # Get directory of command

VERSIONS  = {}                                                                  # Initialize versions dictionary
if latest in cmd:                                                               # If latest string is in the directory path
  root, sub = cmd.split( latest )                                               # Split on the latest string
  if sub[0] == os.sep: sub = sub[1:]                                            # Remove leading /

  vers      = [ver for ver in os.listdir(root) if ver.isdigit()]                # Get list of versions in the latex directory
  dirs      = [os.path.join(root, ver, sub) for ver in vers if ver.isdigit()]   # Build paths to all versions

  VERSIONS.update( dict( zip( vers, dirs ) ) )                                  # Update versions dictionary with versions

VERSIONS[ latest ] = cmd                                                        # Set command

