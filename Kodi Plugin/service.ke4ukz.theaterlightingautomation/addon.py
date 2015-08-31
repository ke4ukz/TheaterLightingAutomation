# Copyright 2015 Jonathan Dean (ke4ukz@gmx.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__name__ = "Theater Lighting Automation" #Script name (also in addon.xml)
__version__ = "1.0.0" #Script version (also in addon.xml)
__author__ = "Jonathan Dean (ke4ukz@gmx.com)" #author information
__addon_id__ = 'service.ke4ukz.theaterlightingautomation' #static ID string for this addon

import serial #For communication over the serial port
import xbmc #For most of what we do through Kodi
import xbmcaddon #So we can get user-changable settings

settings = xbmcaddon.Addon(id=__addon_id__) #Settings object so we can access user-specified settings

def addLogEntry(entry):
	"""Add a log entry to the Kodi log"""
	xbmc.log(__name__ + ": " + entry)

class AutomationHandler(xbmc.Player): #Subclass of xbmc.Player so we can hear the stop/play/pause/resume events

	def __init__ (self):
		"""Initializes the Player object"""
		xbmc.Player.__init__(self)

	def sendCommand(self,command):
		"""Sends the given command over the serial port (appends a newline character to the command)"""
		try:
			self.serialPort.write(command + "\n")
		except Exception as e:
			addLogEntry('Error writing to serial port: ' + str(e) )

	def Run(self):
		"""Run continuously until Kodi tells the addon to abort"""
		while(not xbmc.abortRequested):
			xbmc.sleep(1000)

	def StartUp(self):
		"""Initialize the serial port and turn on the lights"""
		addLogEntry("Starting")
		try:
			self.serialPort = serial.Serial()
			self.serialPort.setPort(settings.getSetting("serialport") )
			self.serialPort.setBaudrate(int(settings.getSetting("baudrate") ) )
			self.serialPort.setByteSize(serial.EIGHTBITS)
			self.serialPort.setParity(serial.PARITY_NONE)
			self.serialPort.setStopbits(serial.STOPBITS_ONE)
			self.serialPort.open()
			xbmc.sleep(2000) #We pause a moment here because the Arduino reboots when the serial port is opened
			self.sendCommand("on")
		except Exception as e:
			addLogEntry("Error opening serial port: " + str(e) )
			return False
		else:
			return True

	def ShutDown(self):
		"""Turn off the lights and close the serial port"""
		addLogEntry("Shutting down")
		try:
			self.sendCommand("off")
			self.serialPort.close()
		except Exception as e:
			addLogEntry("Error closing serial port: " + str(e) )

	def onPlayBackStarted(self):
		"""Set the lights level for video playback (called by Kodi when playback starts)"""
		self.sendCommand("play")

	def onPlayBackEnded(self):
		"""Set the lights level to normal (called by Kodi when playback ends)"""
		self.sendCommand("stop")

	def onPlayBackStopped(self):
		"""Set the lights level to normal (called by Kodi when the user stops playback)"""
		self.sendCommand("stop")

	def onPlayBackPaused(self):
		"""Set the lights level to dim (called by Kodi when playback is paused)"""
		if (settings.getSetting("ignorepause") == "false"):
			self.sendCommand("pause")

	def onPlayBackResumed(self):
		"""Set the lights level for video playback (called by Kodi when playback is resumed from paused)"""
		if (settings.getSetting("ignorepause") == "false"):
			self.sendCommand("resume")

# -- Main Code ----------------------------------------------
handler=AutomationHandler()
if (handler.StartUp() ): #Only run if startup succeeds
	handler.Run() #This function doesn't return until Kodi tells the addon to terminate
	handler.ShutDown() #Clean up and quit
