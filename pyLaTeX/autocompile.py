import logging
import os, signal
from threading import Thread, Event
from queue import Queue
from watchdog.events import FileSystemEventHandler

from .LaTeX import LaTeX

RUNNING = Event()
RUNNING.set()
def sigHandler(*args, **kwargs):
  RUNNING.clear()

class TeXHandler( FileSystemEventHandler ):
  def __init__(self, *args, **kwargs):
    xelatex = kwargs.pop('xelatex', False)
    super().__init__(*args, **kwargs)
    self.__log   = logging.getLogger(__name__)
    self.xelatex = xelatex
    self.queue   = Queue()
    signal.signal( signal.SIGINT,  sigHandler )
    signal.signal( signal.SIGTERM, sigHandler )
    self.thread  = Thread(target=self.__run)
    self.thread.start()
  def on_modified(self, event):
    print(event)
    if event.src_path.endswith('.tex'):
      self.queue.put( event.src_path )
  def join(self, **kwargs):
    self.thread.join(**kwargs)

  def __run(self): 
    self.__log.debug('Compile thread started')
    while RUNNING.is_set():
      try:
        texFile = self.queue.get(timeout = 1.0)
      except:
        continue
      self.__log.info('Compiling file: {}'.format( texFile ))
      print('Compiling file: {}'.format( texFile ))
      l = LaTeX(texFile).compile( xelatex = self.xelatex )
    self.__log.debug('Compile thread stopped')

