#include <ros/ros.h>
#include <can_sim_tc/CanSimNode.h>

int main(int argc, char **argv)
{
    ros::init(argc, argv, "cansim");
    ros::NodeHandle node;
    ros::NodeHandle priv_nh("~");

    if( ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME, ros::console::levels::Debug) )
    {
        ros::console::notifyLoggerLevelsChanged();
    }
    // create CanSimNode class
    can_sim_tc::CanSimNode n(node, priv_nh);

    // handle callbacks until shut down
    ros::spin();

    return 0;
}
