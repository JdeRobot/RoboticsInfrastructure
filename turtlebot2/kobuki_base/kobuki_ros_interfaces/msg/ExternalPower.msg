# Turn on/off Kobuki's external power sources

# Power sources
uint8 PWR_3_3V1A  = 0 # DB25 connector only
uint8 PWR_5V1A    = 1 # DB25 connector and Micro Molex connector
uint8 PWR_12V5A   = 2 # Micro Molex connector only
uint8 PWR_12V1_5A = 3 # Micro Molex connector only

# State
uint8 OFF = 0
uint8 ON  = 1

uint8 source

uint8 state