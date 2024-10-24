--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Ubuntu 16.4-0ubuntu0.24.04.2)
-- Dumped by pg_dump version 16.4 (Ubuntu 16.4-0ubuntu0.24.04.2)

-- SET statement_timeout = 0;
-- SET lock_timeout = 0;
-- SET idle_in_transaction_session_timeout = 0;
-- SET client_encoding = 'UTF8';
-- SET standard_conforming_strings = on;
--SELECT pg_catalog.set_config('search_path', '', false);
--SET check_function_bodies = false;
--SET xmloption = content;
--SET client_min_messages = warning;
--SET row_security = off;

--SET default_tablespace = '';

--SET default_table_access_method = heap;

--
-- Name: universes; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE exercises_world (
    id integer PRIMARY KEY,
    name character varying(100) NOT NULL,
    launch_file_path character varying(200) NOT NULL,
    ros_version character varying(4) NOT NULL,
    visualization character varying(50) NOT NULL,
    world character varying(50) NOT NULL
);

CREATE TABLE exercises_exercise_worlds (
    id integer PRIMARY KEY,
    exercise_id bigint NOT NULL,
    world_id integer REFERENCES exercises_world (id)
);



-- ALTER TABLE public.universes OWNER TO user-dev;

--
-- Data for Name: universes; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY exercises_world (id, name, launch_file_path, ros_version, visualization, world) FROM stdin;
1	autoparking_ros1	/opt/jderobot/Launchers/autoparking.launch	ROS1	gazebo_rae	gazebo
2	basic_vacuum_cleaner_ros2	/opt/jderobot/Launchers/vacuum_cleaner.launch.py	ROS2	gazebo_rae	gazebo
3	obstacle_avoidance_ros1	/opt/jderobot/Launchers/obstacle_avoidance_f1_headless.launch	ROS1	gazebo_rae	gazebo
4	vacuum_cleaner_loc_ros2	/opt/jderobot/Launchers/vacuum_cleaner_loc.launch.py	ROS2	gazebo_rae	gazebo
5	global_navigation_ros2	/opt/jderobot/Launchers/taxi_navigator.launch.py	ROS2	gazebo_rae	gazebo
6	3d_reconstruction_ros1	/opt/jderobot/Launchers/3d_reconstruction_ros.launch	ROS1	gazebo_rae	gazebo
7	rescue_people_ros2	/opt/jderobot/Launchers/world.json	ROS2	gazebo_rae	drones
8	amazon_warehouse_ros2_world1	/opt/jderobot/Launchers/amazon_robot.launch.py	ROS2	gazebo_rae	gazebo
9	follow_line_default_ros1	/opt/jderobot/Launchers/simple_line_follower_ros_headless_default.launch	ROS1	gazebo_rae	gazebo
10	follow_line_default_ros2	/opt/jderobot/Launchers/simple_circuit.launch.py	ROS2	gazebo_rae	gazebo
11	follow_line_montreal_ros2	/opt/jderobot/Launchers/montreal_circuit.launch.py	ROS2	gazebo_rae	gazebo
12	follow_person_ros2	/opt/jderobot/Launchers/follow_person.launch.py	ROS2	gazebo_rae	gazebo
13	follow_person_teleop	/opt/jderobot/Launchers/follow_person_teleop.launch.py	ROS2	gazebo_rae	gazebo
14	autoparking_simple_ackermann_ros2	/opt/jderobot/Launchers/prius_autoparking.launch.py	ROS2	gazebo_rae	gazebo
15	montecarlo_laser_loc_ros2	/opt/jderobot/Launchers/montecarlo_laser_loc.launch.py	ROS2	gazebo_rae	gazebo
16	obstacle_avoidance_ros2	/opt/jderobot/Launchers/simple_circuit_obstacles_followingcam.launch.py	ROS2	gazebo_rae	gazebo
17	global_navigation_followingcam_ros2	/opt/jderobot/Launchers/taxi_navigator_followingcam.launch.py	ROS2	gazebo_rae	gazebo
18	3d_reconstruction_ros2	/opt/jderobot/Launchers/3d_reconstruction.launch.py	ROS2	gazebo_rae	gazebo
19	autoparking_battery_ackermann_ros2	/opt/jderobot/Launchers/prius_bateria.launch.py	ROS2	gazebo_rae	gazebo
20	autoparking_gas_station_line_ackermann_ros2	/opt/jderobot/Launchers/gas_station_line_ackermann.launch.py	ROS2	gazebo_rae	gazebo
21	autoparking_gas_station_battery_ackermann_ros2	/opt/jderobot/Launchers/gas_station_battery_ackermann.launch.py	ROS2	gazebo_rae	gazebo
22	autoparking_gas_station_parking_ackermann_ros2	/opt/jderobot/Launchers/gas_station_parking_ackermann.launch.py	ROS2	gazebo_rae	gazebo
23	amazon_warehouse_ros2_world1_ackermann	/opt/jderobot/Launchers/small_warehouse_with_ackermann_logistic_robot.launch.py	ROS2	gazebo_rae	gazebo
24	amazon_warehouse_ros2_world2_ackermann	/opt/jderobot/Launchers/pallet_warehouse_with_ackermann_logistic_robot.launch.py	ROS2	gazebo_rae	gazebo
25	amazon_warehouse_ros2_world2	/opt/jderobot/Launchers/pallet_warehouse.launch.py	ROS2	gazebo_rae	gazebo
26	follow_line_montmelo_ros2	/opt/jderobot/Launchers/montmelo_circuit.launch.py	ROS2	gazebo_rae	gazebo
27	follow_line_nurburgring_ros2	/opt/jderobot/Launchers/nurburgring_circuit.launch.py	ROS2	gazebo_rae	gazebo
28	follow_line_nurburgring_ack_ros2	/opt/jderobot/Launchers/nurburgring_circuit_ackermann.launch.py	ROS2	gazebo_rae	gazebo
29	follow_line_montmelo_ack_ros2	/opt/jderobot/Launchers/montmelo_circuit_ackermann.launch.py	ROS2	gazebo_rae	gazebo
30	follow_line_montreal_ack_ros2	/opt/jderobot/Launchers/montreal_circuit_ackermann.launch.py	ROS2	gazebo_rae	gazebo
31	follow_line_default_ack_ros2	/opt/jderobot/Launchers/simple_circuit_ackermann.launch.py	ROS2	gazebo_rae	gazebo
\.

COPY exercises_exercise_worlds (id, exercise_id, world_id) FROM stdin;
1	52	1
3	51	2
5	56	4
6	57	5
8	58	7
10	69	8
13	50	10
14	50	9
15	50	11
16	55	12
17	55	13
18	52	14
19	71	15
20  	59	16
21	61	18
22	52	19
23	52	20
24	52	21
25	52	22
26	69	24
27	69	25
28	69	23
29	50	26
30	50	27
31	50	28
32	50	29
33	50	30
34	50	31
\.


--
-- Name: universes universes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

-- ALTER TABLE ONLY public.exercises_world
    -- ADD CONSTRAINT exercises_world_pkey PRIMARY KEY (id);
    
-- ALTER TABLE ONLY public.exercises_exercise_world
    -- ADD CONSTRAINT exercises_exercise_world_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

