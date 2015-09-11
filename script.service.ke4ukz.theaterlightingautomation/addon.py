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

import xbmc #For most of what we do through Kodi
import xbmcaddon #So we can get user-changable settings
import xbmcgui #So we can show notification

#Program information values
__addonname__ = xbmcaddon.Addon().getAddonInfo("name")
__version__ = xbmcaddon.Addon().getAddonInfo("version")
__author__ = xbmcaddon.Addon().getAddonInfo("author")
__addon_id__ = xbmcaddon.Addon().getAddonInfo("id")

def showNotification(header, message, time=4000, icon=xbmcgui.NOTIFICATION_INFO):
	"""Show a notification dialog"""
	xbmcgui.Dialog().notification(header, message, icon, time)

def addLogEntry(entry, loglevel=xbmc.LOGNOTICE):
	"""Add a log entry to the Kodi log"""
	xbmc.log(__addonname__ + ": " + entry, loglevel)

#Import a serial library from somewhere
try:
	#try to use the default pyserial
	import serial
except:
	addLogEntry("Default serial library not found, attempting to use included version", xbmc.LOGWARNING)
	try:
		import os
		import sys
		sys.path.append(os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')) , 'resources', 'lib' ) )
		import serial
	except:
		showNotification(__addonname__, "Unable to load serial library", icon=xbmcgui.NOTIFICATION_ERROR)
		addLogEntry("Unable to load any serial library, sorry", xbmc.LOGFATAL)
		exit()

#Lighting modes
MODE_NORMAL = 0
MODE_PLAYING = 1
MODE_PAUSED = 2
MODE_SCREENSAVER = 3

#Global objects
settings = xbmcaddon.Addon()
serialPort = serial.Serial()

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

def isDuringBlackout(whichLight=""):
	startBlackoutTime = settings.getSetting("startblackouttime")
	endBlackoutTime = settings.getSetting("endblackouttime")
	if (xbmc.getCondVisibility("System.Time(" + startBlackoutTime + ", " + endBlackoutTime + ")") ):
		#during blackout time
		if (whichLight == ""):
			return True
		else:
			if (settings.getSetting("blackout" + whichLight) == "true"):
				#black out this light
				return True
	return False

def initLights():
	"""Initialize lighting to the normal levels"""
	currentMode = getCurrentMode()
	#house
	if (settings.getSetting("controlhouselighting") == "true"):
		#Fade from off to normal
		channel = settings.getSetting("houselightingchannel")
		startlevel = "0"
		if isDuringBlackout("house"):
			endlevel = "0"
		else:
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
		if isDuringBlackout("aisle"):
			endlevel = "0"
		else:
			if currentMode == MODE_NORMAL:
				endlevel = settings.getSetting("normalaislebrightness")
			elif currentMode == MODE_PAUSED:
				endlevel = settings.getSetting("pauseaislebrightness")
			elif currentMode == MODE_PLAYING:
				endlevel = settings.getSetting("playaislebrightness")
			elif currentMode == MODE_SCREENSAVER:
				endlevel = settings.getSetting("ssaislebrightness")
			elif (currentMode == MODE_BLACKOUT) and (settings.getSetting("blackoutaisle") == "true"):
				endlevel = "0"
			else:
				endlevel = "0"
		fadeLights(channel, startlevel, endlevel)
	#ambient
	if settings.getSetting("controlambientlighting") == "true":
		#Fade from off to normal
		channel = settings.getSetting("ambientlightingchannel")
		startlevel = "0"
		if isDuringBlackout("ambient"):
			endlevel = "0"
		else:
			if currentMode == MODE_NORMAL:
				endlevel = settings.getSetting("normalambientbrightness")
			elif currentMode == MODE_PAUSED:
				endlevel = settings.getSetting("pauseambientbrightness")
			elif currentMode == MODE_PLAYING:
				endlevel = settings.getSetting("playambientbrightness")
			elif currentMode == MODE_SCREENSAVER:
				endlevel = settings.getSetting("ssambientbrightness")
			elif (currentMode == MODE_BLACKOUT) and (settings.getSetting("blackoutambient") == "true"):
				endlevel = "0"
			else:
				endlevel = "0"
		fadeLights(channel, startlevel, endlevel)

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
		currentMode = getCurrentMode()
		addLogEntry("Settings changed", xbmc.LOGDEBUG)
		#See if the serial port has been changed
		if (serialPort.getPort() != settings.getSetting("serialport") ) or (serialPort.getBaudrate() != int(settings.getSetting("baudrate") ) ):
			#Close the port and reopen it with the new settings
			addLogEntry("Serial port settings changed, reopening port")
			closePort()
			xbmc.sleep(200) #wait a tick to make sure the port closed
			if openPort():
				initLights()

				houselevel = "0"
		aislelevel = "0"
		ambientlevel = "0"
		if (currentMode == MODE_NORMAL):
			#change brightness for normal
			if (settings.getSetting("controlhouselighting") == "true"):
				if not isDuringBlackout("house"):
					houselevel = settings.getSetting("normalhousebrightness")
				else:
					houselevel = "0"
			if (settings.getSetting("controlaislelighting") == "true"):
				if not isDuringBlackout("aisle"):
					aislelevel = settings.getSetting("normalaislebrightness")
				else:
					aislelevle = "0"
			if (settings.getSetting("controlambientlighting") == "true"):
				if not isDuringBlackout("ambient"):
					ambientlevel = settings.getSetting("normalambientbrightness")
				else:
					ambientlevel = "0"
		elif (currentMode == MODE_PAUSED):
			#change brightness for paused
			if (settings.getSetting("controlhouselighting") == "true"):
				if not isDuringBlackout("house"):
					houselevel = settings.getSetting("pausehousebrightness")
				else:
					houselevel = "0"
			if (settings.getSetting("controlaislelighting") == "true"):
				if not isDuringBlackout("aisle"):
					aislelevel = settings.getSetting("pauseaislebrightness")
				else:
					aislelevle = "0"
			if (settings.getSetting("controlambientlighting") == "true"):
				if not isDuringBlackout("ambient"):
					ambientlevel = settings.getSetting("pauseambientbrightness")
				else:
					ambientlevel = "0"
		elif (currentMode == MODE_PLAYING):
			#change brightness for playing
			if (settings.getSetting("controlhouselighting") == "true"):
				if not isDuringBlackout("house"):
					houselevel = settings.getSetting("playhousebrightness")
					showNotification(__addonname__, "Retrieved play house brightness: " + houselevel, 1000)
				else:
					houselevel = "0"
			if (settings.getSetting("controlaislelighting") == "true"):
				if not isDuringBlackout("aisle"):
					aislelevel = settings.getSetting("playaislebrightness")
				else:
					aislelevle = "0"
			if (settings.getSetting("controlambientlighting") == "true"):
				if not isDuringBlackout("ambient"):
					ambientlevel = settings.getSetting("playambientbrightness")
				else:
					ambientlevel = "0"
		elif (currentMode == MODE_SCREENSAVER):
			#change brightness for screensaver... this shouldn't happen, since the screensaver should be off when settings are being changed
			if (settings.getSetting("controlhouselighting") == "true"):
				if not isDuringBlackout("house"):
					houselevel = settings.getSetting("sshousebrightness")
				else:
					houselevel = "0"
			if (settings.getSetting("controlaislelighting") == "true"):
				if not isDuringBlackout("aisle"):
					aislelevel = settings.getSetting("ssaislebrightness")
				else:
					aislelevle = "0"
			if (settings.getSetting("controlambientlighting") == "true"):
				if not isDuringBlackout("ambient"):
					ambientlevel = settings.getSetting("ssambientbrightness")
				else:
					ambientlevel = "0"

		setLights(settings.getSetting("houselightingchannel"), houselevel)
		setLights(settings.getSetting("aislelightingchannel"), aislelevel)
		setLights(settings.getSetting("ambientlightingchannel"), ambientlevel)

	def onScreensaverActivated(self):
		"""Called when the screen saver kicks in (from xbmc.Monitor)"""
		currentMode = getCurrentMode()
		#fade from normal to screensaver
		if (settings.getSetting("dimonscreensaver") == "true"):
			#aisle
			if (settings.getSetting("controlaislelighting") == "true") and (not isDuringBlackout("aisle") ):
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("normalaislebrightness")
				endlevel = settings.getSetting("ssaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			#house
			if (settings.getSetting("controlhouselighting") == "true") and (not isDuringBlackout("house") ):
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("normalhousebrightness")
				endlevel = settings.getSetting("sshousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#ambient
			if (settings.getSetting("controlambientlighting") == "true") and (not isDuringBlackout("ambient") ):
				channel = settings.getSetting("ambientlightingchannel")
				startlevel = settings.getSetting("normalambientbrightness")
				endlevel = settings.getSetting("ssambientbrightness")
				fadeLights(channel, startlevel, endlevel)

	def onDPMSActivated(self):
		self.onScreensaverActivated()

	def onScreensaverDeactivated(self):
		"""Called when the screensaver goes off (from xbmc.Monitor)"""
		currentMode = getCurrentMode()
		#fade from screensaver to normal
		if (settings.getSetting("dimonscreensaver") == "true"):
			#house
			if (settings.getSetting("controlhouselighting") == "true") and (not isDuringBlackout("house") ):
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("sshousebrightness")
				endlevel = settings.getSetting("normalhousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#aisle
			if (settings.getSetting("controlaislelighting") == "true") and (not isDuringBlackout("aisle") ):
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("ssaislebrightness")
				endlevel = settings.getSetting("normalaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			#ambient
			if (settings.getSetting("controlambientlighting") == "true") and (not isDuringBlackout("ambient") ):
				channel = settings.getSetting("ambientlightingchannel")
				startlevel = settings.getSetting("ssambientbrightness")
				endlevel = settings.getSetting("normalambientbrightness")
				fadeLights(channel, startlevel, endlevel)

	def onDPMSDeactivated(self):
		self.onScreensaverDeactivated()

class AutomationHandler(xbmc.Player): #Subclass of xbmc.Player so we can hear the stop/play/pause/resume events
	def __init__ (self):
		"""Initializes the Player and Monitor objects"""
		xbmc.Player.__init__(self)

	def start(self):
		"""Initialize the serial port and turn on the lights"""
		addLogEntry("Automation Handler starting", xbmc.LOGDEBUG)
		return True

	def stop(self):
		"""Shut down"""
		addLogEntry("Automation Handler stopping", xbmc.LOGDEBUG)

	def onPlayBackStarted(self):
		"""Called by Kodi when playback starts; set the lights level for video playback (from xbmc.Player)"""
		currentMode = getCurrentMode()
		addLogEntry("onPlayBackStarted", xbmc.LOGDEBUG)
		addLogEntry("Current Mode: " + str(currentMode), xbmc.LOGDEBUG)
		
		if currentMode==MODE_PAUSED:
			#fade from pause to play
			self.onPlayBackResumed()
		elif currentMode==MODE_NORMAL:
			#fade from normal to play
			#aisle
			if (settings.getSetting("controlaislelighting") == "true") and (not isDuringBlackout("aisle") ):
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("normalaislebrightness")
				endlevel = settings.getSetting("playaislebrightness")
				fadeLights(channel, startlevel, endlevel)			
			#house
			if (settings.getSetting("controlhouselighting") == "true") and (not isDuringBlackout("house") ):
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("normalhousebrightness")
				endlevel = settings.getSetting("playhousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#ambient
			if (settings.getSetting("controlambientlighting") == "true") and (not isDuringBlackout("ambient") ):
				channel = settings.getSetting("ambientlightingchannel")
				startlevel = settings.getSetting("normalambientbrightness")
				endlevel = settings.getSetting("playambientbrightness")
				fadeLights(channel, startlevel, endlevel)

	def onPlayBackEnded(self):
		"""Called by Kodi when playback ends; Set the lights level to normal (from xbmc.Player)"""
		currentMode = getCurrentMode()
		addLogEntry("onPlayBackEnded", xbmc.LOGDEBUG)
		addLogEntry("Current Mode: " + str(currentMode), xbmc.LOGDEBUG)
		#fade from play to normal
		#house
		if (settings.getSetting("controlhouselighting") == "true") and (not isDuringBlackout("house") ):
			channel = settings.getSetting("houselightingchannel")
			duration = settings.getSetting("fadeduration")
			endlevel = settings.getSetting("normalhousebrightness")
			if (currentMode == MODE_PAUSED):
				startlevel = settings.getSetting("pausehousebrightness")
			else:
				startlevel = settings.getSetting("playhousebrightness")
			fadeLights(channel, startlevel, endlevel)
		#aisle
		if (settings.getSetting("controlaislelighting") == "true") and (not isDuringBlackout("aisle") ):
			channel = settings.getSetting("aislelightingchannel")
			endlevel = settings.getSetting("normalaislebrightness")
			duration = settings.getSetting("fadeduration")
			if (currentMode == MODE_PAUSED):
				startlevel = settings.getSetting("pauseaislebrightness")
			else:
				startlevel = settings.getSetting("playaislebrightness")
			fadeLights(channel, startlevel, endlevel)
		#ambient
		if (settings.getSetting("controlambientlighting") == "true") and (not isDuringBlackout("ambient") ):
			channel = settings.getSetting("ambientlightingchannel")
			endlevel = settings.getSetting("normalambientbrightness")
			duration = settings.getSetting("fadeduration")
			if (currentMode == MODE_PAUSED):
				startlevel = settings.getSetting("pauseambientbrightness")
			else:
				startlevel = settings.getSetting("playambientbrightness")
			fadeLights(channel, startlevel, endlevel)

	def onPlayBackStopped(self):
		"""Called by Kodi when the user stops playback; set the lights level to normal (from xbmc.Player)"""
		addLogEntry("onPlayBackStopped", xbmc.LOGDEBUG)
		self.onPlayBackEnded()

	def onPlayBackPaused(self):
		"""Called by Kodi when playback is paused; set the lights level to dim (from xbmc.Player)"""
		currentMode = getCurrentMode()
		addLogEntry("onPlayBackPaused", xbmc.LOGDEBUG)
		if (settings.getSetting("dimonpause") == "true"):
			#fade from play to paused
			#aisle
			if (settings.getSetting("controlaislelighting") == "true") and (not isDuringBlackout("aisle") ):
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("playaislebrightness")
				endlevel = settings.getSetting("pauseaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			#house
			if (settings.getSetting("controlhouselighting") == "true") and (not isDuringBlackout("house") ):
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("playhousebrightness")
				endlevel = settings.getSetting("pausehousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#ambient
			if (settings.getSetting("controlambientlighting") == "true") and (not isDuringBlackout("ambient") ):
				channel = settings.getSetting("ambientlightingchannel")
				startlevel = settings.getSetting("playambientbrightness")
				endlevel = settings.getSetting("pauseambientbrightness")
				fadeLights(channel, startlevel, endlevel)

	def onPlayBackResumed(self):
		"""Called by Kodi when playback is resumed from paused; set the lights level for video playback (from xbmc.Player)"""
		currentMode = getCurrentMode()
		if (settings.getSetting("dimonpause") == "true"):
			#fade from pause to play
			#house
			if (settings.getSetting("controlhouselighting") == "true") and (not isDuringBlackout("house") ):
				channel = settings.getSetting("houselightingchannel")
				startlevel = settings.getSetting("pausehousebrightness")
				endlevel = settings.getSetting("playhousebrightness")
				fadeLights(channel, startlevel, endlevel)
			#aisle
			if (settings.getSetting("controlaislelighting") == "true") and (not isDuringBlackout("aisle") ):
				channel = settings.getSetting("aislelightingchannel")
				startlevel = settings.getSetting("pauseaislebrightness")
				endlevel = settings.getSetting("playaislebrightness")
				fadeLights(channel, startlevel, endlevel)
			#ambient
			if (settings.getSetting("controlambientlighting") == "true") and (not isDuringBlackout("ambient") ):
				channel = settings.getSetting("ambientlightingchannel")
				startlevel = settings.getSetting("pauseambientbrightness")
				endlevel = settings.getSetting("playambientbrightness")
				fadeLights(channel, startlevel, endlevel)

# -- Main Code ----------------------------------------------
addLogEntry("Started")

playerhandler = AutomationHandler()
monitorhandler = MonitorHandler()

if monitorhandler.start(): #Start the monitor handler and only continue if it succeeds
	if playerhandler.start(): #Only run if startup succeeds
		openPort()
		while( True ): #Wait around for an abort signal from Kodi
			if monitorhandler.waitForAbort(1):
				break
		playerhandler.stop()
	monitorhandler.stop()
	closePort()

addLogEntry("Stopped")
