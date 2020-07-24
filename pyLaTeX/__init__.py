import logging
log = logging.getLogger(__name__)
log.setLevel( logging.DEBUG )
log.addHandler( logging.StreamHandler() )
log.handlers[0].setFormatter(
  logging.Formatter( '%(asctime)s [%(levelname)-4.4s] %(message)s' )
)
