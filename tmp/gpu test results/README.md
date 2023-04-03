
# Gzclient GPU test results

## Commands

* Without GPU
~~~
sudo docker run --name gpu_test --rm -it -p 2303:2303 -p 1905:1905 -p 8765:8765 -p 6080:6080 -p 6081:6081 -p 1108:1108 -p 6082:6082 -p 7163:7163 jderobot/robotics-academy:4.3.1
~~~

* With GPU
~~~
sudo docker run --name gpu_test --device /dev/dri --rm -it -p 2303:2303 -p 1905:1905 -p 8765:8765 -p 6080:6080 -p 6081:6081 -p 1108:1108 -p 6082:6082 -p 7163:7163 jderobot/robotics-academy:4.3.1
~~~