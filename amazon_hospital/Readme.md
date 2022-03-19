# Amazon Hospital

## Usage:
You should include these lines in **$HOME/.bashrc**
~~~
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:<path_to_amazon_hospital>/models
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:<path_to_amazon_hospital>/fuel_models
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:<path_to_amazon_hospital>/hospital_world/models
~~~
where "path_to_amazon_hospital" is the absolute path.

Then, compile and launch the world with the following command:
~~~
ros2 launch hospital_world hospital_world.launch.py
~~~
