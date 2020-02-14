#!/usr/bin/env python3

# A python function to replace figure, table, and equation labels with numbers
import os, re;
import regex
from .utils import recursiveRegex, getEnvironment

CAPTION = regex.compile( r'(\\caption({(?>[^{}]|(?2))*}))' )			# Pattern to grab full \caption{...} command and {...} contents
LABEL   = recursiveRegex( r'\\label', ('{','}') )									# Pattern to grab {...} of \label{} command

class CrossRef(object):
  def __init__(self, label, *args):
    self.label      = label
    self.environs   = args
    self.refs       = {}
    self.num        = []

  def sortEnvirons(self, text):
    '''
    Purpose:
      Method to obtain and sort environments in text based
      on the environments specified and initialization
    Inputs:
      text  : String with contents of tex file
    Keywords:
      None.
    Returns:
      List of environment text, excluding \end{environ}, in order
      of apperance in text
    '''
    pos   = []
    match = []
    for env in self.environs:																									# Iterate over all the environments defined
      env = getEnvironment( env )																							# Create regex pattern for finding environments
      for s in env.finditer( text ):																					# Iterate over all instances of the environment in the text
        pos.append(   s.start() )																							# Append the starting postion of the match to the pos list
        match.append( s.group() )																							# Append the contents of the match to the match list
    if match: match = [m for _, m in sorted( zip(pos, match) ) ]							# Sort the matches based on the starting position
    return match

  def updateCaptions(self, text, environs):  
    i = 0																																			# Initialize counter at zero
    for env in environs:																											# Iterate over sorted matches
      try:																																		# Try to
        label = LABEL.findall( env )[0]
      except:																																	# On exception, just continue
        pass
      else:																																		# On success
        i    += 1																															# Incremnt i
        self.refs.update( {label : i} )

      try:
        command, contents = CAPTION.findall( env )[0]													# Get full caption command and the contents of the caption command
      except:
        pass
      else:
        newContents  = '{{{} {}. {}}}'.format(self.label, i, contents[1:-1])		# Generate new caption contents that contain the object number
        newCommand   = command.replace( contents, newContents )								# Replace old contents in full command with new contents
        newEnv       = env.replace( command, newCommand )											# Replace old command with new command in environment
        text         = text.replace( env, newEnv )														# Replace old evironment with updated environment in text
        label        = LABEL.findall( env )[0]
    return text																																# Return updated text

  def updateRefs(self, text):
    for key, val in self.refs.items():
      key  = '\\ref{}'.format( key )
      text = text.replace( key, '{}'.format(val) )
    return text 

  def process(self, text):
    envs = self.sortEnvirons(text)
    if envs:
      text = self.updateCaptions( text, envs )
      return self.updateRefs( text )
    return text

