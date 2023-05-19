# Folllow intructions in https://kobuki.readthedocs.io/en/release-1.0.x/software.html to install Kobuki from source

> mkdir kobuki && cd kobuki

a virtual environment launcher that will fetch build tools from pypi (colcon, vcstools)
> wget https://raw.githubusercontent.com/kobuki-base/kobuki_documentation/release/1.0.x/resources/venv.bash || exit 1

 custom build configuration options for eigen, sophus
> wget https://raw.githubusercontent.com/kobuki-base/kobuki_documentation/release/1.0.x/resources/colcon.meta || exit 1

 list of repositories to git clone
> wget https://raw.githubusercontent.com/kobuki-base/kobuki_documentation/release/1.0.x/resources/kobuki_standalone.repos || exit 1

> source ./venv.bash

> mkdir src

 vcs handles distributed fetching of repositories listed in a .repos file
> vcs import ./src < kobuki_standalone.repos || exit 1

> deactivate

> source ./venv.bash

Build necessary packages with:
> colcon build --merge-install --packages-select <package> --cmake-args -DBUILD_TESTING=OFF

## list of packages:
ament_cmake        ecl_console          ecl_io              ecl_threads
ament_cmake_ros    ecl_containers       ecl_ipc             ecl_time
ament_cppcheck     ecl_converters       ecl_license         ecl_time_lite
ament_lint         ecl_converters_lite  ecl_linear_algebra  ecl_tools
ament_package      ecl_core             ecl_lite            ecl_type_traits
ament_pycodestyle  ecl_core_apps        ecl_math            ecl_utilities
ament_uncrustify   ecl_devices          ecl_mobile_robot    eigen
COLCON_IGNORE      ecl_eigen            ecl_mpl             kobuki_core
ecl_build          ecl_errors           ecl_sigslots        sophus
ecl_command_line   ecl_exceptions       ecl_sigslots_lite
ecl_concepts       ecl_formatters       ecl_statistics
ecl_config         ecl_geometry         ecl_streams

 update the source workspace
> vcs pull ./src

> deactivate

## KOBUKI RulEs : /dev/ttyUSB0 -> /dev/kobuki
> wget https://raw.githubusercontent.com/kobuki-base/kobuki_ftdi/devel/60-kobuki.rules
> sudo cp 60-kobuki.rules /etc/udev/rules.d

 different linux distros may use a different service manager (this is Ubuntu's)
   --> failing all else, a reboot will work
> sudo service udev reload
> sudo service udev restart

> source ./install/setup.bash

 who is your kobuki?
> kobuki-version-info

 drop into the runtime enviroment
> source ./install/setup.bash

 take kobuki for a test drive
> kobuki-simple-keyop
