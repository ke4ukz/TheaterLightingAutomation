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

import serial #For communication over the serial port
import xbmc #For most of what we do through Kodi
import xbmcaddon #So we can get user-changable settings
import xbmcgui #So we can show notification

#Program information values
__addonname__ = xbmcaddon.Addon().getAddonInfo("name")
__version__ = xbmcaddon.Addon().getAddonInfo("version")
__author__ = xbmcaddon.Addon().getAddonInfo("author")
__addon_id__ = xbmcaddon.Addon().getAddonInfo("id")

#Lighting modes
MODE_NORMAL = 0
MODE_PLAYING = 1
MODE_PAUSED = 2
MODE_SCREENSAVER = 3

#Global objects and variables
settings = xbmcaddon.Addon()
serialPort = serial.Serial()
currentMode = MODE_NORMAL

def showNotification(header, message, time=4000, icon=xbmcgui.NOTIFICATION_INFO):
	"""Show a notification dialog"""
	xbmcgui.Dialog().notification(header, message, icon, time)

def sendCommand(command):
	"""Sends the given command over the serial port (appends a newline character to the command)"""
	addLogEntry("Sending command '" + command + "'", xbmc.LOGDEBUG)
	if serialPort.isOpen():
		try:
			serialPort.write(command + "\n")
		except Exception as e:
			addLogEntry('Error writing to serial port: ' + str(e), xbmc.LOGERROR)
	else:
		addLogEntry("Tried to write to closed serial port", xbmc.LOGWARNING)

def addLogEntry(entry, loglevel=xbmc.LOGNOTICE):
	"""Add a log entry to the Kodi log"""
	xbmc.log(__addonname__ + ": " + entry, loglevel)

def fadeLights(channel, startlevel, endlevel):
	"""Fades the lights on a specified channel using the appropriate method and duration"""
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

def openPort():
	"""Open the serial port and initialize the lights"""
	serialport = settings.getSetting("serialport")
	baudrate = settings.getSetting("baudrate")
	addLogEntry("Opening serial port " + serialport + "@" + baudrate, xbmc.LOGDEBUG)
	if serialPort.isOpen():
		addLogEntry("Tried to open already opened serial port", xbmc.LOGWARNING)
		closePort()

	try:
		serialPort.setPort(serialport)
		serialPort.setBaudrate(int(baudrate) )
		serialPort.setByteSize(serial.EIGHTBITS)
		serialPort.setParity(serial.PARITY_NONE)
		serialPort.setStopbits(serial.STOPBITS_ONE)
		serialPort.open()
		addLogEntry("Serial port successfully opened", xbmc.LOGDEBUG)
		xbmc.sleep(2000) #We pause a moment here because the Arduino reboots when the serial port is opened
		initLights()
	except Exception as e:
		showNotification(__addonname__, settings.getLocalizedString(32000), icon=xbmcgui.NOTIFICATION_ERROR)
		addLogEntry("Error opening serial port: " + str(e), xbmc.LOGERROR)
		return False
	else:
		return True

def closePort():
	"""Shut down the lights and close the serial port"""
	if serialPort.isOpen():
		try:
			addLogEntry("Turning lights off", xbmc.LOGDEBUG)
			sendCommand("alloff")
			addLogEntry("Closing serial port", xbmc.LOGDEBUG)
			serialPort.close()
		except Exception as e:
			addLogEntry("Error closing serial port: " + str(e), xbmc.LOGERROR)
	else:
		addLogEntry("Tried to close already closed serial port", xbmc.LOGWARNING)

def initLights():
	"""Initialize lighting to the normal levels"""
	global currentMode
	#house
	if settings.getSetting("controlhouselighting") == "true":
		#Fade from off to normal
		channel = settings.getSetting("houselightingchannel")
		startlevel = "0"
		if currentMode == MODE_NORMAL:
			endlevel = settings.getSetting("normalhousebrightness")
		elif currentMode == MODE_PAUSED:
			endlevel = settings.getSetting("pausehousebrightness")
		elif currentMode == MODE_PLAYING:
			endlevel = settings.getSetting("playhousebrightness")
		elif currentMode == MODE_SCREENSAVER:
			endlevel = settings.getSetting("sshousebrightness")
		else:
			endlevel = "0"
		fadeLights(channel, startlevel, endlevel)
	#aisle
	if settings.getSetting("controlaislelighting") == "true":
		#Fade from off to normal
		channel = settings.getSetting("aislelightingchannel")
		startlevel = "0"
		if currentMode == MODE_NORMAL:
			endlevel = settings.getSetting("normalaislebrightness")
		elif currentMode == MODE_PAUSED:
			endlevel = settings.getSetting("pauseaislebrightness")
		elif currentMode == MODE_PLAYING:
			endlevel = settings.getSetting("playaislebrightness")
		elif currentMode == MODE_SCREENSAVER:
			endlevel = settings.getSetting("ssaislebrightness")
		else:
			endlevel = "0"
		fadeLights(channel, startlevel, endlevel)
	currentMode = MODE_NORMAL

def getCurrentMode():
	if xbmc.getCondVisibility("System.ScreenSaverActive"):
		return MODE_SCREENSAVER
	elif xbmc.getCondVisibility("Player.Paused"):
		return MODE_PAUSED
	elif xbmc.getCondVisibility("Player.Seeking|Player.Caching|Player.Playing|Player.Forwarding|Player.Rewinding"):
		return MODE_PLAYING
	else:
		return MODE_NORMAL

class MonitorHandler(xbmc.Monitor): #subclass of xbmc.Monitor so we can hear screensaver and settings change events
	def __init__(self):
		"""Initializes the Monitor object"""
		xbmc.Monitor.__init__(self)

	def start(self):
		"""Start up and open the serial port"""
		addLogEntry("Monitor Handler starting", xbmc.LOGDEBUG)
		return True
		
	def stop(self):
		"""Turn off the lights and close the serial port"""
		addLogEntry("Monitor Handler stopping", xbmc.LOGDEBUG)
		
	def onSettingsChanged(self):
		"""Called when the addon settings have been changed (from xbmc.Monitor)"""
		global currentMode
		#See if the serial port has been changed
		addLogEntry("Settings changed", xbmc.LOGDEBUG)
		if (serialPort.getPort() != settings.getSetting("serialport") ) or (serialPort.getBaudrate() != int(settings.getSetting("baudrate") ) ):
			#Close the port and reopen it with the new settings
			addLogEntry("Serial port settings changed, reopening port")
			closePort()
			xbmc.sleep(200) #wait a tick to make sure the port closed
			if openPort():
				initLights()

		if (settings.getSetting("dimonpause") == "false") and (currentMode == MODE_PAUSED):
			currentMode = MODE_NORMAL
		if (settings.getSetting("dimonscreensaver") == "false") and (currentMode == MODE_SCREENSAVER):
			currentMode = MODE_NORMAL
			
		if (currentMode == MODE_NORMAL):
			#change brightness for normal
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("normalhousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("normalaislebrightness"))
		elif (currentMode == MODE_PAUSED):
			#change brightness for paused
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("pausehousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("pauseaislebrightness"))
		elif (currentMode == MODE_PLAYING):
			#change brightness for playing
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("playhousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("playaislebrightness"))
		elif (currentMode == MODE_SCREENSAVER):
			#change brightness for screensaver... this shouldn't happen, since the screensaver should be off when settings are being changed
			if (settings.getSetting("controlhouselighting") == "true"):
				setLights(settings.getSetting("houselightingchannel"), settings.getSetting("sshousebrightness"))
			if (settings.getSetting("controlaislelighting") == "true"):
				setLights(settings.getSetting("aislelightingchannel"), settings.getSetting("ssaislebrightness"))

	def onScreensaverActivated(self):
		"""Called when the screen saver kicks in (from xbmc.Monitor)"""
		global currentMode
		#fade from normal to screensaver
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
		addLogEntry("Automation Handler starting")
		return True

	def stop(self):
		"""Shut down"""
		addLogEntry("Automation Handler stopping")

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
currentMode = getCurrentMode()

if monitorhandler.start(): #Start the monitor handler and only continue if it succeeds
	if playerhandler.start(): #Only run if startup succeeds
		openPort()
		while( True ): #Wait around for an abort signal from Kodi
			if monitorhandler.waitForAbort(1):
				break
		playerhandler.stop()
	monitorhandler.stop()
	closePort()
