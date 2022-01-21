# Contains unique device id, version info and available features for the kobuki platform.
# Useful for compatibility checking and introspection

string hardware   # <major>.<minor>.<patch>
string firmware   # <major>.<minor>.<patch>
string software   # Still to decide how it will look
uint32[] udid

# Bitmask that specifies the available features in the firmware and/or driver
uint64 features

# The following represent the bit fields corresponding to bits in the features value

# Provided firmware kobuki_firmware_1.1.1.hex
uint64 SMOOTH_MOVE_START    = 0000000000000001
uint64 GYROSCOPE_3D_DATA    = 0000000000000002
