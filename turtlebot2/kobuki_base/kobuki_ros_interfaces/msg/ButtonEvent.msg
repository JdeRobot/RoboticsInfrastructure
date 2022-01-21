# Provides a button event.
# This message is generated whenever a particular button is pressed or released.
# Note that, despite buttons field on SensorState messages, state field is not a
# bitmask, but the new state of a single button.

uint8 BUTTON0 = 0
uint8 BUTTON1 = 1
uint8 BUTTON2 = 2

uint8 RELEASED = 0
uint8 PRESSED  = 1

uint8 button
uint8 state
