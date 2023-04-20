#include <boost/bind.hpp>
#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <iostream>
#include <chrono>
#include <vector>
#include <tuple>
#include <cmath>
#include <thread>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <err.h>

/**
 * SOCKET FUNCTIONS description (teleop)
 **/
int create_socket(void);
void close_socket(int fd);
void set_ip_port(struct sockaddr_in & addr, const char * ip, int port);
void make_bind(int fd, struct sockaddr_in & addr);
int recv_message(int fd, struct sockaddr_in & dest_addr, void * buf, size_t len);


const float PI = 3.14159265;
const int QUADRANTS = 4;
const std::string IP = "0.0.0.0";
const int PORT = 36677;

namespace gazebo
{
    class Person : public ModelPlugin
    {

    private:

        int state, current_wp;
        int turn_dir, linear_dir;
        bool auto_movement, linear_movement;
        float lv_dt = 0.002; // discrete lineal velocity
        float av_dt = 0.003; // discrete angular velocity

        // variables to use in MoveToWaypoint method
        bool orientation_reached = false;
        bool direction_chosen = false;
        
        physics::ModelPtr model;
        event::ConnectionPtr updateConnection;

        // waypoints where (px, py, next_waypoint)
        std::vector <std::tuple<float, float, int>> wp;

        // quadrants vector to know the correct direction of turn
        std::vector <std::tuple<float, float>> quadrants;

        // The server will receive velocity commands from client to move the model
        int sockfd;
        struct sockaddr_in addr;
        std::thread server_thread;


    private:

        float GetDistanceEuclidean(float rx, float ry)
        {
            auto pose = this->model->WorldPose();

            return sqrt(pow(pose.Pos().X() - rx, 2) + pow(pose.Pos().Y() - ry, 2));
        }


        float GetDistanceEuclidean(std::tuple <float, float, int> & waypoint)
        {
            int wx = std::get<0>(waypoint);
            int wy = std::get<1>(waypoint);
            
            return GetDistanceEuclidean(wx, wy);
        }


        int GetNearestWaypoint(std::vector < std::tuple<float, float, int> > & waypoints)
        {
            float current_dist;
            int nearest_index = 0;
            float min_dist = GetDistanceEuclidean(waypoints[0]);
            
            for (size_t i = 0; i < waypoints.size(); i++) {
                current_dist = GetDistanceEuclidean(waypoints[i]);
                if (current_dist < min_dist) {
                    min_dist = current_dist;
                    nearest_index = i;
                }
            }

            return nearest_index;
        }


        float GetAngle(float rx, float ry)
        {
            // Returns the Angle in Radians

            auto pose = this->model->WorldPose();
            float angle = atan2(abs(rx - pose.Pos().X()), abs(ry - pose.Pos().Y()));

            if (ry > pose.Pos().Y()) {
                angle = PI - angle;
            }
            if (rx < pose.Pos().X()) {
                angle *= -1;
            }
            return angle;
        }


        int GetBestTurnDirection(float desired_yaw, float actual_yaw)
        {
            auto get_quadrant = [](int yaw, std::vector<std::tuple<float, float>> & quadrants) {
                // iterate over all quadrants (4)
                for (std::size_t i = 0; i < QUADRANTS; i++) {
                    if (yaw >= std::get<0>(quadrants[i]) && yaw < std::get<1>(quadrants[i])) {
                        return i;
                    }
                }
            };

            // Search the corresponding quadrants
            int actual_quadrant = get_quadrant(actual_yaw, this->quadrants);
            int desired_quadrant = get_quadrant(desired_yaw, this->quadrants);

            // both angles share the same quadrant
            if (actual_quadrant == desired_quadrant) {
                return (desired_yaw > actual_yaw) ? 1 : -1; 
            }

            /** 
             * Calculate distance between angles in different quadrants
             * n1 -> quadrants of separation between the yaw angles for distance 1
             * n2 -> quadrants of separation between the yaw angles for distance 2
             **/
            int n1, n2, dist1, dist2;

            n1 = (desired_quadrant > actual_quadrant) ?
                  desired_quadrant - actual_quadrant :
                  QUADRANTS - abs((desired_quadrant - actual_quadrant) % QUADRANTS);
            n2 = QUADRANTS - n1;

            // Calculating Distance 1
            dist1 = std::get<1>(quadrants[actual_quadrant]) - actual_yaw;
            for (int i = 0; i < (n1 - 1); i++) {
                dist1 += PI/2;
            }
            dist1 += desired_yaw - std::get<0>(quadrants[desired_quadrant]);

            // Calculating Distance 2
            dist2 = actual_yaw - std::get<0>(quadrants[actual_quadrant]);
            for (int i = 0; i < (n2 - 1); i++) {
                dist2 += PI/2;
            }
            dist2 += std::get<1>(quadrants[desired_quadrant]) - desired_yaw;

            // Return best direction
            return (dist1 <= dist2) ? 1 : -1;
        }


        bool MoveToWaypoint(std::tuple<float, float, int> & waypoint)
        {
            float rx = std::get<0>(waypoint);
            float ry = std::get<1>(waypoint);
            float angle = GetAngle(rx, ry);
            auto pose = this->model->WorldPose();

            /**
             * Procedure for moving to the next waypoint
             **/
            // First, it will determine the orientation of turn
            if (!direction_chosen) {
                direction_chosen = true;
                turn_dir = GetBestTurnDirection(angle, pose.Rot().Yaw());
            }
            // Second, It will turn until Yaw desired is reached
            if (!orientation_reached) {
                pose.Rot() = ignition::math::Quaterniond(0, 0, pose.Rot().Yaw() + turn_dir*av_dt);
                if (abs(angle - pose.Rot().Yaw()) < 0.005) {
                    orientation_reached = true;
                }
            }
            // Third, it will move to position desired
            else {
                pose.Pos().X() += -lv_dt * (0*cos(pose.Rot().Yaw()) - 1*sin(pose.Rot().Yaw()));
                pose.Pos().Y() += -lv_dt * (0*sin(pose.Rot().Yaw()) + 1*cos(pose.Rot().Yaw()));
            }
            this->model->SetWorldPose(pose);

            if (orientation_reached && GetDistanceEuclidean(rx, ry) < 0.1) {
                // Reset static boolean values;
                orientation_reached = false;
                direction_chosen = false;
                return true;
            }
            return false;
        }

        void ServerThreadLoop(void)
        {
            char msg[3];

            while (true) {
                recv_message(this->sockfd, this->addr, &msg, sizeof msg);
                
                if (msg[0] == 'U') {
                    auto_movement = false;

                    if (msg[1] == 'V') {
                        linear_movement = true;
                        if (msg[2] == 'F') {
                            linear_dir = 1;
                        }
                        else if (msg[2] == 'B') {
                            linear_dir = -1;
                        }
                    }
                    else if (msg[1] == 'A') {
                        linear_movement = false;
                        if (msg[2] == 'R') {
                            turn_dir = -1;
                        }
                        else if (msg[2] == 'L') {
                            turn_dir = 1;
                        }
                    }
                    else if (msg[1] == 'S') {
                        linear_dir = 0;
                        turn_dir = 0;
                    }
                }
                else if (msg[0] == 'A') {
                    current_wp = GetNearestWaypoint(this->wp);
                    auto_movement = true;
                    orientation_reached = false;
                    direction_chosen = false;
                }
            }
        }


    public:

        virtual ~Person()
        {
            this->ModelPlugin::~ModelPlugin();
            close_socket(this->sockfd);
        }


        void Load(physics::ModelPtr _parent, sdf::ElementPtr)
        {
            this->model = _parent;
            this->updateConnection = event::Events::ConnectWorldUpdateBegin(
                boost::bind(&Person::OnUpdate, this, _1));

            std::cout << "Initial Position Person [" << this->model->WorldPose() << "]\n";

            // Setting WayPoints
            current_wp = 0;
            wp = {
                std::make_tuple(4, 6, 1),
                std::make_tuple(5, 3, 2),
                std::make_tuple(5, -14.5, 3),
                std::make_tuple(-5, -14.5, 4),
                std::make_tuple(-5, -25, 5),
                std::make_tuple(5, -25, 6),
                std::make_tuple(5, -14.5, 7),
                std::make_tuple(-5, -14.5, 8),
                std::make_tuple(-5, -1, 9),
                std::make_tuple(-4, 2, 10),
                std::make_tuple(-4, 5, 11),
                std::make_tuple(-2.5, 13, 12),
                std::make_tuple(3, 13, 13),
                std::make_tuple(4, 10, 0),
            };

            quadrants = {
                std::make_tuple(0.0, PI/2),
                std::make_tuple(PI/2, PI),
                std::make_tuple(-PI, -PI/2),
                std::make_tuple(-PI/2, 0.0)
            };

            auto_movement = false;
            linear_movement = true;
            linear_dir = 0;
            
            // Initializing Server
            this->sockfd = create_socket();
            set_ip_port(this->addr, IP.c_str(), PORT);
            make_bind(this->sockfd, this->addr);
            server_thread = std::thread(&Person::ServerThreadLoop, this);
        }


        void OnUpdate(const common::UpdateInfo &)
        {
            if (auto_movement) {
                if (MoveToWaypoint(wp[current_wp])) {
                    current_wp = std::get<2>(wp[current_wp]);
                }
            }
            else {
                auto pose = this->model->WorldPose();
                if (linear_movement) {
                    pose.Pos().X() += -(linear_dir)*lv_dt * (0*cos(pose.Rot().Yaw()) - 1*sin(pose.Rot().Yaw()));
                    pose.Pos().Y() += -(linear_dir)*lv_dt * (0*sin(pose.Rot().Yaw()) + 1*cos(pose.Rot().Yaw()));
                }
                else {
                    pose.Rot() = ignition::math::Quaterniond(0, 0, pose.Rot().Yaw() + turn_dir*av_dt);
                }
                this->model->SetWorldPose(pose);
            }
        }
    };
    GZ_REGISTER_MODEL_PLUGIN(Person)
}

/**
 * SOCKETS FUNCTIONS Definitions
 **/

int create_socket(void)
{
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd == -1) {
        err(1, "socket failed");
    }
    return fd;
}


void close_socket(int fd)
{
    if (close(fd) == -1) {
        err(1, "close failed");
    }
}


void set_ip_port(struct sockaddr_in & addr, const char * ip, int port)
{
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr(ip);
    addr.sin_port = htons(port);
}


void make_bind(int fd, struct sockaddr_in & addr)
{
    if (bind(fd, (struct sockaddr *)&addr, sizeof addr) == -1) {
        err(1, "bind failed");
    }
}


int recv_message(int fd, struct sockaddr_in & dest_addr, void * buf, size_t len)
{
    socklen_t socklen = sizeof dest_addr;
    if (recvfrom(fd, buf, len, 0, (struct sockaddr *)&dest_addr, &socklen) == -1) {
        warn("recvfrom failed");
        return 1;
    }
    return 0;
}
