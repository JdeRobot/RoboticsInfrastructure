# Provides a cliff sensor event.
# This message is generated whenever a particular cliff sensor signals that the
# robot approaches or moves away from a cliff.
# Note that, despite cliff field on SensorState messages, state field is not a
# bitmask, but the new state of a single sensor.

# cliff sensor
uint8 LEFT   = 0
uint8 CENTER = 1
uint8 RIGHT  = 2

# cliff sensor state
uint8 FLOOR = 0
uint8 CLIFF = 1

uint8 sensor
uint8 state

# distance to floor when cliff was detected
uint16 bottom