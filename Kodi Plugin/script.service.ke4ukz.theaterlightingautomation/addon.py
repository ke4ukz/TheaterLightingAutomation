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
__version__ = "1.1.0" #Script version (also in addon.xml)
__author__ = "Jonathan Dean (ke4ukz@gmx.com)" #author information
__addon_id__ = 'script.service.ke4ukz.theaterlightingautomation' #static ID string for this addon

import serial #For communication over the serial port
import xbmc #For most of what we do through Kodi
import xbmcaddon #So we can get user-changable settings
import xbmcgui #So we can show notification

MODE_NORMAL = 0
MODE_PLAYING = 1
MODE_PAUSED = 2
MODE_SCREENSAVER = 3

settings = xbmcaddon.Addon() #Settings object so we can access user-specified settings
serialPort = serial.Serial()
currentMode = MODE_NORMAL

def showNotification(header, message, time=4000, icon=xbmcgui.NOTIFICATION_INFO):
	xbmcgui.Dialog().notification(header, message, icon, time)

def sendCommand(command):
	"""Sends the given command over the serial port (appends a newline character to the command)"""
	addLogEntry("Sending command '" + command + "'", xbmc.LOGDEBUG)
	try:
		serialPort.write(command + "\n")
	except Exception as e:
		addLogEntry('Error writing to serial port: ' + str(e) )

def addLogEntry(entry, loglevel=xbmc.LOGNOTICE):
	"""Add a log entry to the Kodi log"""
	xbmc.log(__name__ + ": " + entry, loglevel)
#	if (loglevel == xbmc.LOGDEBUG):
#		showNotification(__name__, entry, 1000)

def fadeLights(channel, startlevel, endlevel):
	"""Fades the lights on a specified channel using the appropriate method and duration"""
	#addLogEntry("Fading from " + startlevel + " to " + endlevel, xbmc.LOGDEBUG)
	startlevel = int(2.55 * int(startlevel))
	endlevel = int(2.55 * int(endlevel))
	duration = int(float(settings.getSetting("fadeduration"))* 1000)
	if endlevel > startlevel:
		method = "exponential "
	else:
		method = "logarithmic "
	sendCommand(method + channel + "," + str(startlevel) + "," + str(endlevel) + "," + str(duration))

def setLights(channel, level):
	"""Sets the lights on a specified channel immediately to a given level"""
	sendCommand("set " + channel + "," + str(int(2.55 * int(level))))

class MonitorHandler(xbmc.Monitor):
	def __init__(self):
		"""Initializes the Monitor object"""
		xbmc.Monitor.__init__(self)

	def start(self):
		"""Start up and open the serial port"""
		addLogEntry("Monitor starting", xbmc.LOGDEBUG)
		return self.openPort()
		
	def stop(self):
		"""Turn off the lights and close the serial port"""
		addLogEntry("Monitor stopping", xbmc.LOGDEBUG)
		try:
			sendCommand("alloff")
			addLogEntry("Closing serial port", xbmc.LOGDEBUG)
			serialPort.close()
		except Exception as e:
			addLogEntry("Error closing serial port: " + str(e) )
		
	def openPort(self):
		"""Open the serial port"""
		serialport = settings.getSetting("serialport")
		baudrate = settings.getSetting("baudrate")
		addLogEntry("Opening serial port " + serialport + "@" + baudrate, xbmc.LOGDEBUG)
		try:
			serialPort.setPort(serialport)
			serialPort.setBaudrate(int(baudrate) )
			serialPort.setByteSize(serial.EIGHTBITS)
			serialPort.setParity(serial.PARITY_NONE)
			serialPort.setStopbits(serial.STOPBITS_ONE)
			serialPort.open()
			addLogEntry("Serial port successfully opened", xbmc.LOGDEBUG)
			xbmc.sleep(2000) #We pause a moment here because the Arduino reboots when the serial port is opened
			self.initLights()
		except Exception as e:
			showNotification(__name__, settings.getLocalizedString(32000), icon=xbmcgui.NOTIFICATION_ERROR)
			addLogEntry("Error opening serial port: " + str(e) )
			return False
		else:
			return True

	def initLights(self):
		"""Initialize lighting to the normal levels"""
		#house
		if settings.getSetting("controlhouselighting") == "true":
			#Fade from off to normal
			channel = settings.getSetting("houselightingchannel")
			startlevel = "0"
			endlevel = settings.getSetting("normalhousebrightness")
			fadeLights(channel, startlevel, endlevel)

		#aisle
		if settings.getSetting("controlaislelighting") == "true":
			#Fade from off to normal
			channel = settings.getSetting("aislelightingchannel")
			startlevel = "0"
			endlevel = settings.getSetting("normalaislebrightness")
			fadeLights(channel, startlevel, endlevel)
		currentMode = MODE_NORMAL

	def onSettingsChanged(self):
		"""Called when the addon settings have been changed (from xbmc.Monitor)"""
		global currentMode
		#See if the serial port has been changed
		addLogEntry("Settings changed", xbmc.LOGDEBUG)
		if (serialPort.getPort() != settings.getSetting("serialport") ) or (serialPort.getBaudrate() != int(settings.getSetting("baudrate") ) ):
			#Close the port and reopen it with the new settings
			addLogEntry("Serial port settings changed, reopening port")
			serialPort.close()
			xbmc.sleep(200) #wait a tick to make sure the port closed
			if self.openPort():
				self.initLights()

		if (settings.getSetting("dimonpause") == "false") and (currentMode == MODE_PAUSED):
			currentMode = MODE_NORMAL
		if (settings.getSetting("dimonscreensaver") == "false") and (currentMode == MODE_SCREENSAVER):
			currentMode = MODE_NORMAL
			
		if (currentMode == MODE_NORMAL):
			#addLogEntry("Setting normal brightness", xbmc.LOGDEBUG)
			#change brightness for normal
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("normalhousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("normalaislebrightness"))
		elif (currentMode == MODE_PAUSED):
			#addLogEntry("Setting paused brightness", xbmc.LOGDEBUG)
			#change brightness for paused
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("pausehousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("pauseaislebrightness"))
		elif (currentMode == MODE_PLAYING):
			#addLogEntry("Setting playing brightness", xbmc.LOGDEBUG)
			#change brightness for playing
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("playhousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("playaislebrightness"))
		elif (currentMode == MODE_SCREENSAVER):
			#addLogEntry("Setting screensaver brightness", xbmc.LOGDEBUG)
			#change brightness for screensaver
			#This shouldn't happen, since the screensaver should be off when settings are being changed
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("sshousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("ssaislebrightness"))

	def onScreensaverActivated(self):
		"""Called when the screen saver kicks in (from xbmc.Monitor)"""
		global currentMode
		#fade from normal to screensaver
		#addLogEntry("Screensaver activated", xbmc.LOGDEBUG)
		if (settings.getSetting("dimonscreensaver") == "true"):
			#aisle
			if settings.getSetting("controlaislelighting") == "true":
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("normalaislebrightness")
				endlevel = settings.getSetting("ssaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			#house
			if settings.getSetting("controlhouselighting") == "true":
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("normalhousebrightness")
				endlevel = settings.getSetting("sshousebrightness")
				fadeLights(channel, startlevel, endlevel)
			currentMode = MODE_SCREENSAVER
	
	def onScreensaverDeactivated(self):
		"""Called when the screensaver goes off (from xbmc.Monitor)"""
		global currentMode
		#fade from screensaver to normal
		#addLogEntry("Screensaver deactivated", xbmc.LOGDEBUG)
		if (settings.getSetting("dimonscreensaver") == "true"):
			#house
			if settings.getSetting("controlhouselighting") == "true":
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("sshousebrightness")
				endlevel = settings.getSetting("normalhousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#aisle
			if settings.getSetting("controlaislelighting") == "true":
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("ssaislebrightness")
				endlevel = settings.getSetting("normalaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			currentMode = MODE_NORMAL
	
class AutomationHandler(xbmc.Player): #Subclass of xbmc.Player so we can hear the stop/play/pause/resume events
	def __init__ (self):
		"""Initializes the Player and Monitor objects"""
		xbmc.Player.__init__(self)
		
	def start(self):
		"""Initialize the serial port and turn on the lights"""
		addLogEntry("Starting")
		return True

	def stop(self):
		"""Shut down"""
		addLogEntry("Shutting down")

	def onPlayBackStarted(self):
		"""Called by Kodi when playback starts; set the lights level for video playback (from xbmc.Player)"""
		global currentMode
		addLogEntry("onPlayBackStarted", xbmc.LOGDEBUG)
		addLogEntry("Current Mode: " + str(currentMode), xbmc.LOGDEBUG)
		
		if currentMode==MODE_PAUSED:
			#fade from pause to play
			self.onPlayBackResumed()
		elif currentMode==MODE_NORMAL:
			#fade from normal to play
			#aisle
			if settings.getSetting("controlaislelighting") == "true":
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("normalaislebrightness")
				endlevel = settings.getSetting("playaislebrightness")
				fadeLights(channel, startlevel, endlevel)			
			#house
			if settings.getSetting("controlhouselighting") == "true":
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("normalhousebrightness")
				endlevel = settings.getSetting("playhousebrightness")
				fadeLights(channel, startlevel, endlevel)
			currentMode = MODE_PLAYING
		
	def onPlayBackEnded(self):
		"""Called by Kodi when playback ends; Set the lights level to normal (from xbmc.Player)"""
		global currentMode
		addLogEntry("onPlayBackEnded", xbmc.LOGDEBUG)
		addLogEntry("Current Mode: " + str(currentMode), xbmc.LOGDEBUG)
		#fade from play to normal
		#house
		if settings.getSetting("controlhouselighting") == "true":
			channel = settings.getSetting("houselightingchannel")
			duration = settings.getSetting("fadeduration")
			endlevel = settings.getSetting("normalhousebrightness")
			if (currentMode == MODE_PAUSED):
				startlevel = settings.getSetting("pausehousebrightness")
			else:
				startlevel = settings.getSetting("playhousebrightness")
			fadeLights(channel, startlevel, endlevel)

		#aisle
		if settings.getSetting("controlaislelighting") == "true":
			channel = settings.getSetting("aislelightingchannel")
			endlevel = settings.getSetting("normalaislebrightness")
			duration = settings.getSetting("fadeduration")
			if (currentMode == MODE_PAUSED):
				startlevel = settings.getSetting("pauseaislebrightness")
			else:
				startlevel = settings.getSetting("playaislebrightness")
			fadeLights(channel, startlevel, endlevel)
		currentMode = MODE_NORMAL
		
	def onPlayBackStopped(self):
		"""Called by Kodi when the user stops playback; set the lights level to normal (from xbmc.Player)"""
		addLogEntry("onPlayBackStopped", xbmc.LOGDEBUG)
		self.onPlayBackEnded()

	def onPlayBackPaused(self):
		"""Called by Kodi when playback is paused; set the lights level to dim (from xbmc.Player)"""
		global currentMode
		addLogEntry("onPlayBackPaused", xbmc.LOGDEBUG)
		if (settings.getSetting("dimonpause") == "true"):
			currentMode = MODE_PAUSED
			#fade from play to paused
			#aisle
			if settings.getSetting("controlaislelighting") == "true":
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("playaislebrightness")
				endlevel = settings.getSetting("pauseaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			#house
			if settings.getSetting("controlhouselighting") == "true":
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("playhousebrightness")
				endlevel = settings.getSetting("pausehousebrightness")
				fadeLights(channel, startlevel, endlevel)

	def onPlayBackResumed(self):
		"""Called by Kodi when playback is resumed from paused; set the lights level for video playback (from xbmc.Player)"""
		global currentMode
		if (settings.getSetting("dimonpause") == "true"):
			#fade from pause to play
			
			#house
			if settings.getSetting("controlhouselighting") == "true":
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("pausehousebrightness")
				endlevel = settings.getSetting("playhousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#aisle
			if settings.getSetting("controlaislelighting") == "true":
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("pauseaislebrightness")
				endlevel = settings.getSetting("playaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			currentMode = MODE_PLAYING

# -- Main Code ----------------------------------------------
playerhandler = AutomationHandler()
monitorhandler = MonitorHandler()
if monitorhandler.start(): #Start the monitor handler and only continue if it succeeds
	if playerhandler.start(): #Only run if startup succeeds
		while( True ):
			if monitorhandler.waitForAbort(1):
				break
		playerhandler.stop()
		monitorhandler.stop()