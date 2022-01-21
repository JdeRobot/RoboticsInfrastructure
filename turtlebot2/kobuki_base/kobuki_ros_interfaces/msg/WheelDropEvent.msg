# Provides a wheel drop event.
# This message is generated whenever one of the wheels is dropped (robot fell
# or was raised) or raised (normal condition).
# Note that, despite wheel_drop field on SensorState messages, state field is
# not a bitmask, but the new state of a single sensor.

# wheel
uint8 LEFT  = 0
uint8 RIGHT = 1

# state
uint8 RAISED  = 0
uint8 DROPPED = 1

uint8 wheel
uint8 state
