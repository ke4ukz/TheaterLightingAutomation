#define __NAME__ "TheaterLights"    //Software name
#define __VERSION__ "1.0.2"         //Software version

#define null 0                      //null value (wasn't defined anywhere else)

#define PIN_HOUSE_LED 3             //Hardware pin to which house lights are connected
#define PIN_AISLE_LED 5             //Hardware pin to which aisle lights are connected

#define STATE_STOP 0                //Player is stopped
#define STATE_PLAY 1                //Player is playing
#define STATE_PAUSE 2               //Player is paused

#define HELP_STRING "Commands:\n\ton\n\toff\n\tplay\n\tstop\n\tpause\n\tresume\n\thelp" //String to send back when 'help' is received on the serial port

//Byte arrays for fading light levels
//Fade down from full-on to full-off
byte fadeDownFull[] = {255,215,191,175,162,151,142,134,128,122,116,111,106,102,98,94,91,87,84,81,79,76,73,71,68,66,64,62,60,58,56,54,52,51,49,47,46,44,43,41,40,38,37,36,34,33,32,31,29,28,27,26,25,24,23,22,21,20,19,18,17,16,15,14,13,12,11,10,10,9,8,7,6,6,5,4,3,2,1,0};
//Fade up from full-off to full-on
byte fadeUpFull[] = {0,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,4,4,4,5,5,5,6,6,7,7,8,8,9,10,10,11,12,13,14,15,16,17,19,20,21,23,25,27,28,31,33,35,38,41,44,47,50,54,58,62,67,72,77,83,89,95,102,109,117,126,135,145,156,167,179,192,206,221,237,255};
//Fade down from dim-on to full-off
byte fadeDownLow[] = {32,27,24,22,21,19,18,17,16,16,15,14,14,13,13,12,12,12,11,11,10,10,10,10,9,9,9,8,8,8,8,7,7,7,7,7,6,6,6,6,6,6,5,5,5,5,5,5,4,4,4,4,4,4,4,4,3,3,3,3,3,3,3,3,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,0};
//Fade up from full-off to dim-on
byte fadeUpLow[] = {1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,8,8,8,9,9,9,10,10,11,11,12,12,13,13,14,15,15,16,17,17,18,19,20,21,22,23,24,25,26,27,28,29,31,32};

int currentState = STATE_STOP; //current player state

//processCommand: accepts a String and acts according to the command indicated.
//Much of the conditional logic is to prevent weird lighting in the event that a command is missed. Sometimes Kodi will go straight from play to play, so we
//want to make sure that we don't pop the lights on only to fade them out again
void processCommand(String command) {
  if (command.equals("") ) return; //Quit now if no command was passed
  if (command.equalsIgnoreCase("play") ) { //Player has started playing
    if (currentState == STATE_STOP) { //Can only play if we're stopped
      currentState = STATE_PLAY; //Set current player state
      fadeLights(fadeDownFull, fadeUpLow); //House lights fade to off, aisle lights to low
    }
  } else if (command.equalsIgnoreCase("stop") ) { //Player has stopped
    if (currentState == STATE_PAUSE) { //Special case for stopping from pause
      currentState = STATE_STOP; //Set current state to stopped
      fadeLights(fadeUpFull, fadeDownFull, 50); //House lights to full from 32 (index 50), aisle lights to off from 32 (index 50)
    } else if (currentState == STATE_PLAY) { //Only run if the player is currently playing
      currentState = STATE_STOP; //Set current state to stopped
      fadeLights(fadeUpFull, fadeDownLow); //House lights to full, aisle lights to off
    }
  } else if (command.equalsIgnoreCase("pause") ) { //Playback has been paused
    if (currentState == STATE_PLAY) { //Only react if the player was playing
      currentState = STATE_PAUSE; //Set current state to paused
      fadeLights(fadeUpLow, null); //House lights to low, don't change aisle lights
    }
  } else if (command.equalsIgnoreCase("resume") ) { //Playback has resumed from paused
    if (currentState == STATE_PAUSE) { //Only react if the player was paused
      currentState = STATE_PLAY; //Set current state to playing
      fadeLights(fadeDownLow, null); //House lights to off, don't change aisle lights
    }
  } else if (command.equalsIgnoreCase("on") ) { //Turn on house lights (received when the service starts on the player)
    digitalWrite(PIN_HOUSE_LED, HIGH); //House lights to full
    digitalWrite(PIN_AISLE_LED, LOW); //Aisle lights off
  } else if (command.equalsIgnoreCase("off") ) { //Turn off house lights (received when the service stops on the player)
    digitalWrite(PIN_HOUSE_LED, LOW); //House lights off
    digitalWrite(PIN_AISLE_LED, LOW); //Aisle lights off
  } else if (command.equalsIgnoreCase("help") ) { //The user has asked for help
    Serial.println(HELP_STRING); //Send them a list of commands
  } else { //We received a command we don't recognize
    Serial.print("Unknown command: "); //Tell the user the command was unknown
    Serial.println(command); //and echo it back
  }
}

//fadeLights: plays the specified light fade scheme
//This method is overridden to make the startFrom value optional
void fadeLights(byte *houseList, byte *aisleList) {
  fadeLights(houseList, aisleList, 0); //Call the other fadeLights method with the given fading schemes and zero start-index
}
void fadeLights(byte *houseList, byte *aisleList, byte startFrom) {
  for (int fadeIndex=startFrom; fadeIndex<80; fadeIndex++) { //Go from the specified index to the last one, 79
    if (houseList != null) //If a list was passed for the house lights...
      analogWrite(PIN_HOUSE_LED, houseList[fadeIndex]); //Write the PWM value for the current fading scheme index to the house lights pin
    if (aisleList != null) //If a list was passed for the aisle lights...
      analogWrite(PIN_AISLE_LED, aisleList[fadeIndex]); //Write the PWM value for the current fading scheme index to the aisle lights pin
    delay(15); //Slow down the fade
  }
}

//setup: Called once when the device starts
void setup() {
  Serial.begin(57600); //Open serial port
  Serial.print(__NAME__); //Print program name
  Serial.print(" version ");
  Serial.print(__VERSION__); //Print program version
  Serial.print(" (");
  Serial.print(__DATE__); //Print compile date
  Serial.println(")");
  
  pinMode(PIN_HOUSE_LED, OUTPUT); //Set house lights pin to output
  pinMode(PIN_AISLE_LED, OUTPUT); //Set aisle lights pin to output
  digitalWrite(PIN_HOUSE_LED, LOW); //Start up with house lights turned off
  digitalWrite(PIN_AISLE_LED, LOW); //Start up with aisle lights turned off
}

//loop: called over and over forever
void loop() {
  //We don't do anything here, everything is driven from serialEvent()
}

//serialEvent: This event is called whenever there is new data in the input buffer
void serialEvent() {
  String inBuffer; //Buffer to hold the input string
  while (Serial.available() > 0) { //While there is something in the serial input buffer...
    inBuffer = Serial.readStringUntil('\n'); //Read to the first newline 
    processCommand(inBuffer); //Pass the value to processCommand
  }
}

