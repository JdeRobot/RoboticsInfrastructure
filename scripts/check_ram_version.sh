#!/bin/bash

# Function to get the GPU device path based on vendor priority
get_curr_version() {
    echo "Current version: $(pip show robotics_application_manager | egrep -o '([0-9]+\.){2}[0-9]+' | head -n 1)"
    return 0
}


# Get the GPU device path based on priority and set DRI_NAME
echo -e "\n--- Robotics Application Manager info ---"
get_curr_version
echo -e "-----------------------------\n"
