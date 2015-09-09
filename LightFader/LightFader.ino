/*************************************************************************
    LightFader - Fades lights using various fading curves
    Copyright (C) 2015 Jonathan Dean (ke4ukz@gmx.com)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*************************************************************************/

#define __NAME__ "LightFader"
#define __VERSION__ "1.1.1"

#define HELPMESSAGE "Commands:\nhelp\nexponential channel,from,to,time\nlogarithmic channel,from,to,time\nlinear channel,from,to,time\nset channel,value\nget channel\nlist\nalloff\nUnambiguous abbreviations are also accepted"
      
#define FADE_NONE 0
#define FADE_LINEAR 1
#define FADE_EXPONENTIAL 2
#define FADE_LOGARITHMIC 3

#define NUM_CHANNELS 2
byte channels[] = {3, 5}; //Arduino pin number for each channel

//These will all be zero-initialized and set to a size based on NUM_CHANNELS
byte values[NUM_CHANNELS] = {0};
byte fadeModes[NUM_CHANNELS] = {0};
unsigned long startTimes[NUM_CHANNELS] = {0};
unsigned long durations[NUM_CHANNELS] = {0};
int aValues[NUM_CHANNELS] ={0};
float bValues[NUM_CHANNELS] = {0};

/***************************************************************
splitInts - Splits a list of numbers separated by a given delimiter into an array of ints 
  String tosplit:    The string to split into pieces
  char delim:        The character to use as a delimiter
  int maxitems:      Maximum number of items to carve out of the string
  int* values        Array of ints to store the found values
  
  Returns (int)      The number of items found
****************************************************************/
int splitInts(String tosplit, char delim, int maxitems, int* values) {
  int delimAt, lastDelim = 0, i;
  for (i=0; i<maxitems; i++) {
    delimAt = tosplit.indexOf(delim);
    if (delimAt > 0) {
      values[i] = tosplit.substring(0, delimAt).toInt();
      tosplit = tosplit.substring(delimAt+1);
    } else if (delimAt == 0) {
      values[i] = 0;
      tosplit = tosplit.substring(1);
    } else {
      values [i] = tosplit.toInt();
      return i+1;
    }
  }
  return i;
}

/***************************************************************
setChannel - Sets the PWM value for a channel
  int channel      The channel to set (between 0 and NUM_CHANNELS-1
  int value        The value to set the channel to (0-255)
  
  Returns:         None
***************************************************************/
void setChannel(int channel, int value) {
  if ( (channel >=0) && (channel < NUM_CHANNELS) ) {
    value = constrain(value, 0, 255);
    fadeModes[channel] = FADE_NONE; //Turn off any fade effect that may be going on
    analogWrite(channels[channel], value);
    values[channel] = value;
  }
}

/***************************************************************
getChannel - Gets the PWM value for a channel and prints it over the serial port
  int channel      The channel to get the value of (between 0 and NUM_CHANNELS-1
  
  Returns (int):   The value of the channel, or -1 if the channel does not exist
***************************************************************/
int getChannel(int channel) {
  if ( (channel >=0) && (channel < NUM_CHANNELS) ) {
    Serial.print("Channel ");
    Serial.print(channel);
    Serial.print(" (pin ");
    Serial.print(channels[channel]);
    Serial.print(") = ");
    Serial.println(values[channel]);
    return values[channel];
  } else {
    Serial.print("Invalid channel");
    return -1;
  }
}

/***************************************************************
linearFade - Sets fade values for a linear curve
  int channel      The channel to set (between 0 and NUM_CHANNELS-1
  int from         Starting value (0-255)
  int to           Ending value (0-255)
  int time         Time to spend fading in milliseconds
  
  Returns:         None
  Notes:           This method may be used to fade both directions, up and down
***************************************************************/
void linearFade(int channel, int from, int to, int time) {
  //y = a + b * x
  if ( (channel >=0) && (channel < NUM_CHANNELS) && (time > 0) ) {
    aValues[channel] = from;
    bValues[channel] = (to - from) / (float)time;
    startTimes[channel] = millis();
    durations[channel] = time;
    fadeModes[channel] = FADE_LINEAR;
  }
}

/***************************************************************
exponentialFade - Fades a channel using an exponential curve
  int channel      The channel to set (between 0 and NUM_CHANNELS-1
  int from         Starting value (0-255)
  int to           Ending value (0-255)
  int time         Time to spend fading in milliseconds
  
  Returns:         None
  Notes:           the value for from must be less than to in order to get a fade
***************************************************************/
void exponentialFade(int channel, int from, int to, int time) {
  //y = a * b ^ x
  if ( (channel >=0) && (channel < NUM_CHANNELS) && (time > 0) ) {
    //This equation won't work with zeroes, so we'll make them ones
    if (from == 0)
      from = 1;
    if (to == 0)
      to = 1;
    aValues[channel] = from;
    bValues[channel] = pow( (to/(float)from), (1.0F / time));
    startTimes[channel] = millis();
    durations[channel] = time;
    fadeModes[channel] = FADE_EXPONENTIAL;
  }
}

/***************************************************************
logarithmicFade - Fades a channel using a logarithmic curve
  int channel      The channel to set (between 0 and NUM_CHANNELS-1
  int from         Starting value (0-255)
  int to           Ending value (0-255)
  int time         Time to spend fading in milliseconds
  
  Returns:         None
  Notes:           the value for from must be greater than to in order to get a fade
***************************************************************/
void logarithmicFade(int channel, int from, int to, int time) {
  //y = a + b * ln(x)
  if ( (channel >=0) && (channel < NUM_CHANNELS) && (time > 0) ) {
    aValues[channel] = from;
    bValues[channel] = (to - from) / log(time);
    startTimes[channel] = millis();
    durations[channel] = time;
    fadeModes[channel] = FADE_LOGARITHMIC;
  }
}


/***************************************************************
processCommand - Acts according to a command givem
  String command   The command to process
  
  Returns:         None
  Notes:           This method does the bulk of the work figuring out what the user wants to do
***************************************************************/
void processCommand(String command) {
  int spaceAt;
  int argValues[5];
  String task, params;
  if (command.endsWith("\r") )
    command = command.substring(0, command.length() - 1);
  spaceAt = command.indexOf(' ');
  if (spaceAt >= 0) {
    task = command.substring(0, spaceAt);
    params = command.substring(spaceAt + 1);

    if (task.equalsIgnoreCase("set") || task.equalsIgnoreCase("s") ) {
      if (splitInts(params, ',', 2, argValues) == 2) {
        setChannel(argValues[0], argValues[1]);
      } else {
        Serial.println("Invalid arguments");
      }
    } else if (task.equalsIgnoreCase("get") || task.equalsIgnoreCase("g") ) {
      getChannel(params.toInt() );
    } else if (task.equalsIgnoreCase("exponential") || task.equalsIgnoreCase("e") ) {
      if (splitInts(params, ',', 4, argValues) == 4) {
        exponentialFade(argValues[0], argValues[1], argValues[2], argValues[3]);
      } else {
        Serial.println("Invalid arguments");
      }      
    } else if (task.equalsIgnoreCase("linear") || task.equalsIgnoreCase("lin") ) {
      if (splitInts(params, ',', 4, argValues) == 4) {
        linearFade(argValues[0], argValues[1], argValues[2], argValues[3]);
      } else {
        Serial.println("Invalid arguments");
      }      
    } else if (task.equalsIgnoreCase("logarithmic") || task.equalsIgnoreCase("lo") ) {
      if (splitInts(params, ',', 4, argValues) == 4) {
        logarithmicFade(argValues[0], argValues[1], argValues[2], argValues[3]);
      } else {
        Serial.println("Invalid arguments");
      }      
    } else {
      Serial.println("Unknown command");
    }
  } else {
    if (command.equalsIgnoreCase("help") || command.equalsIgnoreCase("h") ) {
      Serial.println(HELPMESSAGE);
    } else if (command.equalsIgnoreCase("list") || command.equalsIgnoreCase("lis") ) {
      for (int i=0; i<NUM_CHANNELS; i++) {
        getChannel(i);
      }
    } else if (command.equalsIgnoreCase("alloff") || command.equalsIgnoreCase("a") ) {
      for (int i=0; i<NUM_CHANNELS; i++) {
        digitalWrite(channels[i], LOW);
        values[i] = 0;
        fadeModes[i] = FADE_NONE;
      }
    } else {
      Serial.println("Unknown command");
    }
  }
}

/***************************************************************
fadeStep - Calculates and applies the next lighting step value for the given channel
  int channel      The channel to step
  
  Returns:         None
***************************************************************/
void fadeStep(int channel) {
  int y;
  unsigned long x;
  
  //Quit early if we don't fade this channel
  if (fadeModes[channel] == FADE_NONE)
    return;
    
  x = millis() - startTimes[channel];
  if (x > durations[channel]) {
    //We've run out of time, so make sure it's set to the full value
    x = durations[channel];
  }

  switch(fadeModes[channel]) {
    case FADE_LINEAR:
      // y = a + b * x
      y = aValues[channel] + bValues[channel] * x;
      break;
    case FADE_EXPONENTIAL:
      //y = a * b ^ x
     y = aValues[channel] * pow(bValues[channel], x);
      break;
    case FADE_LOGARITHMIC:
      //y = a + b * ln(x)
      y = aValues[channel] + bValues[channel] * log(x);
      break;
    default: //Shouldn't happen, but saves us from setting an invalid y-value in case it does
      return;
      break;
  }

  if (x == durations[channel]) {
    //Last iteration, so turn off further fading
    fadeModes[channel] = FADE_NONE;
  }
  
  //Make sure we didn't go over or under the valid range for byte
  y = constrain(y, 0, 255);

  //Don't change the value if it's the same thing to reduce flickering
  if (y != values[channel]) {
    analogWrite(channels[channel], y);
    values[channel] = (byte)y;
  }

}

/***************************************************************
setup - Initialize and start things
  
  Returns:         None
  Notes:           This method is called once when the device is reset
***************************************************************/
void setup() {
  Serial.begin(57600);
  Serial.print(__NAME__);
  Serial.print(" version ");
  Serial.print(__VERSION__);
  Serial.print(" (");
  Serial.print(__DATE__);
  Serial.println(")");
  for (int i=0; i<NUM_CHANNELS; i++) {
    pinMode(channels[i], OUTPUT);
  }
}

/***************************************************************
loop - Runs continually as long as the device is powered on
  Returns:         None
  Notes:           This method is called again as soon as it is finished, thus running the code in it over and over
***************************************************************/
void loop() {
  //Go through each channel and step its fade (if necessary)
  for (int i=0; i<NUM_CHANNELS; i++) {
    fadeStep(i);
  }
}

/***************************************************************
serialEvent - Handles new data arriving on the serial port  
  Returns:         None
  Notes:           This method is called every time data arrives over the serial port
***************************************************************/
void serialEvent(void) {
  String inBuffer = "";
  while (Serial.available() ) {
    inBuffer = Serial.readStringUntil('\n');
    processCommand(inBuffer);
  }
}
