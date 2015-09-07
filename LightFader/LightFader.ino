/*  LightFader - Fades lights using various fading curves
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
    along with this program.  If not, see <http://www.gnu.org/licenses/>.*/
    
#define __NAME__ "LightFader"
#define __VERSION__ "1.0.0"

#define NUM_CHANNELS 2

byte channels[] = {3, 5};
byte values[] = {0, 0};

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
  if (channel < NUM_CHANNELS) {
    analogWrite(channels[channel], value);
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
    Serial.print(": ");
    Serial.println(values[channel]);
    return values[channel];
  } else {
    Serial.print("Invalid channel");
    return -1;
  }
}

/***************************************************************
linearFade - Fades a channel using a linear curve
  int channel      The channel to set (between 0 and NUM_CHANNELS-1
  int from         Starting value (0-255)
  int to           Ending value (0-255)
  int time         Time to spend fading in milliseconds
  
  Returns:         None
  Notes:           This method may be used to fade both directions, up and down
***************************************************************/
void linearFade(int channel, int from, int to, int time) {
  //y = m * x + b
  float m;
  unsigned long startTime, x;
  int y, b;
  if ( (from != to) && (time > 0) ) {
    m = (to - from) / (float)time;
    b = from;
    startTime = millis();
    do {
      x = millis() - startTime;
      y = m * x + b;
      analogWrite(channels[channel], y);
    } while (x < time);
  }
  analogWrite(channels[channel], to);
  values[channel] = to;
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
  //y = a + b ^ x
  int a, y;
  double b;
  unsigned long startTime, x;

  if ( (to > from) && (time > 0) ) {
    a = from - 1;
    b = pow( (to - from + 1),  (1 / (double)time) );
    startTime = millis();
    do {
      x = millis() - startTime;
      y = a + pow(b, x);
      analogWrite(channels[channel], y);
    } while (x < time);
  }
  analogWrite(channels[channel], to);
  values[channel] = to;
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
  unsigned long startTime, x;
  int a, y;
  float b;
  
  if ( (to < from) && (time > 0) ) {
    a = from;
    b = (to - from) / log(time);
    startTime = millis();
    do {
      x = millis() - startTime;
      if (x != 0) {
        y = a + b * log(x);
        analogWrite(channels[channel], y);
      }
    } while (x < time);
    analogWrite(channels[channel], to);
    values[channel] = to;
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
  spaceAt = command.indexOf(' ');
  if (spaceAt >= 0) {
    task = command.substring(0, spaceAt);
    params = command.substring(spaceAt + 1);

    if (task.equalsIgnoreCase("set") ) {
      if (splitInts(params, ',', 2, argValues) == 2) {
        setChannel(argValues[0], argValues[1]);
      } else {
        Serial.println("Invalid arguments");
      }
    } else if (task.equalsIgnoreCase("get") ) {
      getChannel(params.toInt() );
    } else if (task.equalsIgnoreCase("exponential") ) {
      if (splitInts(params, ',', 4, argValues) == 4) {
        exponentialFade(argValues[0], argValues[1], argValues[2], argValues[3]);
      } else {
        Serial.println("Invalid arguments");
      }      
    } else if (task.equalsIgnoreCase("linear") ) {
      if (splitInts(params, ',', 4, argValues) == 4) {
        linearFade(argValues[0], argValues[1], argValues[2], argValues[3]);
      } else {
        Serial.println("Invalid arguments");
      }      
    } else if (task.equalsIgnoreCase("logarithmic") ) {
      if (splitInts(params, ',', 4, argValues) == 4) {
        logarithmicFade(argValues[0], argValues[1], argValues[2], argValues[3]);
      } else {
        Serial.println("Invalid arguments");
      }      
    } else {
      Serial.println("Unknown command");
    }
  } else {
    if (command.equalsIgnoreCase("help") ) {
      Serial.println("Commands:");
      Serial.println("help");
      Serial.println("exponential channel,from,to,time");
      Serial.println("logarithmic channel,from,to,time");
      Serial.println("linear channel,from,to,time");
      Serial.println("set channel,value");
      Serial.println("get channel");
      Serial.println("list");
      Serial.println("alloff");
    } else if (command.equalsIgnoreCase("list") ) {
      for (int i=0; i<NUM_CHANNELS; i++) {
        getChannel(i);
      }
    } else if (command.equalsIgnoreCase("alloff") ) {
      for (int i=0; i<NUM_CHANNELS; i++) {
        digitalWrite(channels[i], LOW);
      }
    } else {
      Serial.println("Unknown command");
    }
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
  //Nothing done in here, everything is driven from data arriving over the serial port
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
