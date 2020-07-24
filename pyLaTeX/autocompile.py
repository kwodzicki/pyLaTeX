import logging
import os, sys, time, signal
from threading import Thread, Event, Lock
from queue import Queue
from watchdog.events import FileSystemEventHandler

from .LaTeX import LaTeX

RUNNING = Event()
RUNNING.set()
def sigHandler(*args, **kwargs):
  RUNNING.clear()

class TeXHandler( FileSystemEventHandler ):
  def __init__(self, **kwargs):
    super().__init__()
    signal.signal( signal.SIGINT,  sigHandler )
    signal.signal( signal.SIGTERM, sigHandler )
    self.__log       = logging.getLogger(__name__)
    self.kwargs      = kwargs
    self.queue       = Queue()
    self.compileLock = Lock()
    self.compiling   = Event()
    self.thread      = Thread(target=self.__run)
    self.thread.start()

  def isTeX(self, filePath):
    return filePath.endswith('tex')

  def isSwap(self, filePath):
    if sys.platform == 'linux':
      return False
    return filePath.endswith('.swp')

  def swapToFile(self, filePath):
    fileDir, fileName = os.path.split( filePath )
    fileName, fileExt = os.path.splitext( fileName )
    return os.path.join( fileDir, fileName[1:] ) 

  def on_modified(self, event):
    if not event.is_directory:
      self.__log.debug( event )
      self.queue.put( event.src_path )

  def join(self, **kwargs):
    self.thread.join(**kwargs)

  def __compile(self, texFile):
    with self.compileLock:
      if self.compiling.is_set():
        self.__log.debug("Already compiling, have to wait")
        return
      else:
        self.compiling.set()

    l = LaTeX(texFile).compile( **self.kwargs )
    time.sleep(0.5)
    self.compiling.clear()

  def __run(self): 
    self.__log.debug('Compile thread started')
    while RUNNING.is_set():
      try:
        filePath = self.queue.get(timeout = 1.0)
      except:
        continue

      if self.isSwap( filePath ):
        filePath = self.swapToFile( filePath )
      if self.isTeX( filePath ):
        Thread( target = self.__compile, args=(filePath,) ).start()

    self.__log.debug('Compile thread stopped')

