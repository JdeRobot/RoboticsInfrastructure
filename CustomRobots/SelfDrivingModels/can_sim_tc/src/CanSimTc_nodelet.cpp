#include <pluginlib/class_list_macros.h>
#include <nodelet/nodelet.h>

#include <can_sim_tc/CanSimNode.h>

namespace can_sim_tc
{

class CanSimTcNodeletClass : public nodelet::Nodelet
{
public:
  CanSimTcNodeletClass()
  {
  }
  ~CanSimTcNodeletClass()
  {
  }

  void onInit(void)
  {
    node_.reset(new CanSimNode(getNodeHandle(), getPrivateNodeHandle()));
  }

private:
  boost::shared_ptr<CanSimNode> node_;
};

} // namespace dbw_mkz_can

// Register this plugin with pluginlib.  Names must match nodelets.xml.
//
// parameters: package, class name, class type, base class type
PLUGINLIB_DECLARE_CLASS(can_sim_tc, CanSimTcNodeletClass, can_sim_tc::CanSimTcNodeletClass, nodelet::Nodelet);