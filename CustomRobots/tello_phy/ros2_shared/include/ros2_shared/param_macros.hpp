#ifndef PARAM_MACROS_HPP
#define PARAM_MACROS_HPP

#include <algorithm>
#include <string>
#include <vector>

#include <rclcpp/node.hpp>

// A set of macros that help define parameters in ROS2 nodes. The ROS2 infrastructure keeps parameters
// internal to the node. These macros allow the parameter values to be stored in accessible members that
// are kept in sync with the node internal values.
//
//  1) Define a master macro with containing the full list of parameters.
//  2) Define and initialize the member parameter variables with the PAMA_PARAMS_DEFINE macro.
//  3) Register the parameters with ROS2 with the PAMA_PARAMS_INIT macro.
//  4) Setup a callback to update member variables when internal parameters change with PAMA_PARAMS_CHANGED.
//  5) Display the values of all parameters with the PAMA_PARAMS_LOG macro.
//  6) Check that all the command line arguments are defined parameters.
//
// Sample code that demonstrates one way to use these macros.
#if 0 // beginning of sample code

#define LOC_ALL_PARAMS \
  /* Aruco markers */\
  PAMA_PARAM(aruco_dictionary_id, int, 0)             /* Aruco dictionary id for localization markers  */ \
  PAMA_PARAM(cv3_do_corner_refinement, int, 1)        /* OpenCV 3.x argument to detect corners. 0 = false, 1 = true */\
  PAMA_PARAM(cv4_corner_refinement_method, int, 2)    /* OpenCV 4.x argument to detect corners. 0 = none, 1 = subpix, 2 = contour, 3 = apriltag */\
  /* End of list */

struct LocContext
{
#undef PAMA_PARAM
#define PAMA_PARAM(n, t, d) PAMA_PARAM_DEFINE(n, t, d)
  PAMA_PARAMS_DEFINE(LOC_ALL_PARAMS)
};

void validate_parameters()
{}

void setup_parameters()
{
#undef PAMA_PARAM
#define PAMA_PARAM(n, t, d) PAMA_PARAM_INIT(n, t, d)
  PAMA_PARAMS_INIT((*this), cxt_, "vloc.", LOC_ALL_PARAMS, validate_parameters)

#undef PAMA_PARAM
#define PAMA_PARAM(n, t, d) PAMA_PARAM_CHANGED(n, t, d)
  PAMA_PARAMS_CHANGED((*this), cxt_, "vloc.", LOC_ALL_PARAMS, validate_parameters, RCLCPP_INFO)

#undef PAMA_PARAM
#define PAMA_PARAM(n, t, d) PAMA_PARAM_LOG(n, t, d)
  PAMA_PARAMS_LOG((*this), cxt_, "vloc.", LOC_ALL_PARAMS, RCLCPP_INFO)

#undef PAMA_PARAM
#define PAMA_PARAM(n, t, d) PAMA_PARAM_CHECK_CMDLINE(n, t, d)
  PAMA_PARAMS_CHECK_CMDLINE((*this), "vloc.", LOC_ALL_PARAMS, RCLCPP_ERROR)

  // An example of how to set a parameter from code.
  PAMA_SET_PARAM((*this), cxt_, "vloc.", cv3_do_corner_refinement, 0);
}
#endif // End of sample code



// ==============================================================================
// Define parameters
// ==============================================================================

// Define PAMA_PARAM to PAMA_PARAM_DEFINE before invoking PAMA_PARAMS_DEFINE
#define PAMA_PARAM_DEFINE(n, t, d) t n##_{d};

#define PAMA_PARAMS_DEFINE(all_params) \
  all_params \
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr pama_callback_handle_{};


// ==============================================================================
// Declare parameters
// ==============================================================================

// Define PAMA_PARAM to PAMA_PARAM_INIT before invoking PAMA_PARAMS_INIT
#define PAMA_PARAM_INIT(n, t, d) \
  _c.n##_ = _n.declare_parameter(_p+#n, _c.n##_);

// Initialize the parameter members from the node
#define PAMA_PARAMS_INIT(node_ref, cxt_ref, pre_str, all_params, validate_func) \
{ \
  auto &_c = cxt_ref; auto &_n = node_ref; \
  std::string _p{pre_str}; \
  all_params \
  validate_func(); \
}


// ==============================================================================
// Register for parameter changed notification (by external sources)
// ==============================================================================

// Define PAMA_PARAM to PAMA_PARAM_CHANGED before invoking PAMA_PARAMS_CHANGED
#define PAMA_PARAM_CHANGED(n, t, d) \
if (parameter.get_name() == _p+#n) { \
  param_set = true; \
  _c.n##_ = parameter.get_value<t>(); \
  log_func(_p+#n, rclcpp::to_string(rclcpp::ParameterValue{_c.n##_})); \
}

// Register for parameter changed notifications
#define PAMA_PARAMS_CHANGED(node_ref, cxt_ref, pre_str, all_params, validate_func, logger_macro) \
{auto log_func = [&_n = node_ref](const std::string & n, const std::string & v) { \
    logger_macro(_n.get_logger(), "Parameter %s value changed to %s", n.c_str(), v.c_str());}; \
cxt_ref.pama_callback_handle_ = node_ref.add_on_set_parameters_callback( \
[this, log_func](const std::vector<rclcpp::Parameter> &parameters) -> rcl_interfaces::msg::SetParametersResult \
{ \
  auto result = rcl_interfaces::msg::SetParametersResult(); \
  bool param_set{false}; \
  auto &_c = cxt_ref; \
  std::string _p{pre_str};  \
  for (const auto &parameter : parameters) { \
    all_params \
  } \
  if (param_set) { validate_func(); } \
  result.successful = true; \
  return result; \
});}


// ==============================================================================
// Log the current parameter values
// ==============================================================================

// Define PAMA_PARAM to PAMA_PARAM_LOG before invoking PAMA_PARAMS_LOG
#define PAMA_PARAM_LOG(n, t, d)  ps.emplace_back(std::string(_p+#n).append(" = ") \
  .append(rclcpp::to_string(rclcpp::ParameterValue{_c.n##_}).c_str()));

#define PAMA_PARAMS_LOG(node_ref, cxt_ref, pre_str, all_params, logger_macro) \
{ \
  std::vector<std::string> ps{}; \
  auto &_c = cxt_ref; \
  std::string _p{pre_str}; \
  all_params \
  std::sort(ps.begin(), ps.end()); \
  std::string s{pre_str}; s.append(" params"); \
  for (auto &p : ps) { \
    s.append("\n").append(p); \
  } \
  logger_macro(node_ref.get_logger(), s.c_str()); \
}


// ==============================================================================
// Check for parameters that were on the command line but are not defined. (Often a command line mis-type)
// ==============================================================================

// Define PAMA_PARAM to PAMA_PARAM_CHECK_CMDLINE and then use the
// PAMA_PARAMS_CHECK_CMDLINE marco to display invalid/undefined command line parameters.
#define PAMA_PARAM_CHECK_CMDLINE(n, t, d) if ((npo.first == _p+#n) || \
  (!_p.empty() && npo.first.rfind(_p, 0) == std::string::npos)) continue;

#define PAMA_PARAMS_CHECK_CMDLINE(node_ref, pre_str, all_params, logger_macro) { \
  auto npi = get_node_parameters_interface(); \
  auto npos = npi->get_parameter_overrides(); \
  std::string _p{pre_str}; \
  for (auto &npo : npos) { \
    all_params \
    if (npo.first == "use_sim_time") continue; \
    logger_macro(node_ref.get_logger(), "**** ERROR: Undefined command line parameter: %s", npo.first.c_str()); \
  } \
}


// ==============================================================================
// Set a parameter's value
// ==============================================================================

// Use PAMA_SET_PARAM to set the local and node's parameter value
#define PAMA_SET_PARAM(node_ref, cxt_ref, pre_str, n, d) \
  do { \
  cxt_ref.n##_ = d; \
  node_ref.set_parameter(rclcpp::Parameter(std::string(pre_str)+#n, d)); \
  } while (false)


#endif //PARAM_MACROS_HPP
