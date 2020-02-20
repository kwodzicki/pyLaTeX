import logging
import os, signal
from threading import Thread, Event, Timer
from queue import Queue
from watchdog.events import FileSystemEventHandler

from .LaTeX import LaTeX

RUNNING = Event()
RUNNING.set()
def sigHandler(*args, **kwargs):
  RUNNING.clear()

def compiler( texFile, **kwargs ):
  l = LaTeX(texFile)
  l.compile( **kwargs )
  
class TeXHandler( FileSystemEventHandler ):
  def __init__(self, **kwargs):
    super().__init__()
    self.__log   = logging.getLogger(__name__)
    self.kwargs  = kwargs
    self.queue   = Queue()
    signal.signal( signal.SIGINT,  sigHandler )
    signal.signal( signal.SIGTERM, sigHandler )
    self.thread  = Thread(target=self.__run)
    self.thread.start()
    self.timer   = None

  def isTeX(self, filePath):
    return filePath.endswith('tex')

  def isSwap(self, filePath):
    return filePath.endswith('.swp')

  def swapToFile(self, filePath):
    fileDir, fileName = os.path.split( filePath )
    fileName, fileExt = os.path.splitext( fileName )
    return os.path.join( fileDir, fileName[1:] ) 

  def on_modified(self, event):
    if not event.is_directory:
      self.__log.debug( event )
      filePath = event.src_path
      if self.isSwap( filePath ):
        filePath = self.swapToFile( filePath )
      if self.isTeX( filePath ):
        self.queue.put( filePath )

  def join(self, **kwargs):
    self.thread.join(**kwargs)

  def __run(self): 
    self.__log.debug('Compile thread started')
    while RUNNING.is_set():
      try:
        texFile = self.queue.get(timeout = 1.0)
      except:
        continue
      l = LaTeX(texFile).compile( **self.kwargs )
      #if self.timer and not self.timer._started.is_set():
      #  self.timer.cancel()
      #self.timer = Timer(2.0, compiler, args=(texFile,), kwargs={'xelatex' : self.xelatex})
      #self.timer.start()
    self.__log.debug('Compile thread stopped')

