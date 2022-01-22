# Kobuki Sensor Data Messages
#
# For more direct simple interactions (buttons, leds, gyro, motor velocity
# etc) use the other topics. This provides detailed information about the
# entire state package that is transmitted at 50Hz from the robot.
#


###### CONSTANTS ######
# Bumper states (states are combined, when multiple bumpers are pressed)
uint8 BUMPER_RIGHT  = 1
uint8 BUMPER_CENTRE = 2
uint8 BUMPER_LEFT   = 4

# Wheel drop sensor states (states are combined, when both wheel drop sensors are triggered)
uint8 WHEEL_DROP_RIGHT = 1
uint8 WHEEL_DROP_LEFT  = 2

# Cliff sensor states (states are combined, when multiple cliff sensors are triggered)
uint8 CLIFF_RIGHT  = 1
uint8 CLIFF_CENTRE = 2
uint8 CLIFF_LEFT   = 4

# Button states (only one button can be triggered at a time)
uint8 BUTTON0 = 1
uint8 BUTTON1 = 2
uint8 BUTTON2 = 4

# Charger state is a combination of charging device (adapter, docking station)
# and state (charging, charged, discharging):
uint8 DISCHARGING      = 0
uint8 DOCKING_CHARGED  = 2
uint8 DOCKING_CHARGING = 6
uint8 ADAPTER_CHARGED  = 18
uint8 ADAPTER_CHARGING = 22

# Over current states
uint8 OVER_CURRENT_LEFT_WHEEL  = 1
uint8 OVER_CURRENT_RIGHT_WHEEL = 2
uint8 OVER_CURRENT_BOTH_WHEELS = 3

# Digital input states (states are combined, when multiple inputs are set at the same time)
# When connecting Yujin's test board, it acts as pull-up what inverts the behaviour:
# No input: 79, all inputs set (e.g. buttons pressed): 64
uint8 DIGITAL_INPUT0 = 1
uint8 DIGITAL_INPUT1 = 2
uint8 DIGITAL_INPUT2 = 4
uint8 DIGITAL_INPUT3 = 8
uint8 DB25_TEST_BOARD_CONNECTED = 64

###### MESSAGE ######

std_msgs/Header header

###################
# Core Packet
###################
uint16 time_stamp      # milliseconds starting when turning on Kobuki (max. 65536, then starts from 0 again)
uint8  bumper          # see bumper states
uint8  wheel_drop      # see wheel drop sensor states
uint8  cliff           # see cliff sensor states
uint16 left_encoder    # accumulated ticks left wheel starting with turning on Kobuki (max. 65535)
uint16 right_encoder   # accumulated ticks right wheel starting with turning on Kobuki (max. 65535)
int8   left_pwm        # % of applied maximum voltage left wheel: -100 (max. voltage backward) to +100 (max. voltage forward)
int8   right_pwm       # % of applied maximum voltage right wheel: -100 (max. voltage backward) to +100 (max. voltage forward)
uint8  buttons         # see button states
uint8  charger         # see charger states
uint8  battery         # battery voltage in 0.1V (ex. 16.1V -> 161)

###################
# Cliff Packet
###################
uint16[] bottom        # ADC output of the right, centre, left cliff PSD sensor (0 - 4095, distance measure is non-linear)

###################
# Current Packet
###################
uint8[] current        # motor current for the left and right motor in 10mA (ex. 12 -> 120mA)
uint8   over_current   # see over current states

###################
# Input Packet
###################
uint16   digital_input # see digital input states; will show garbage when nothing is connected
uint16[] analog_input  # ADC values for the 4 analog inputs; 0 - 4095: 0.0 - 3.3V; will show garbage when nothing is connected
