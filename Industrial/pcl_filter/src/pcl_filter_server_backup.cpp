#include <rclcpp/rclcpp.hpp>
#include <pcl/point_types.h>
#include <pcl/ModelCoefficients.h>
#include <pcl/filters/extract_indices.h>
#include <pcl/filters/passthrough.h>
#include <pcl/features/normal_3d.h>
#include <pcl/sample_consensus/method_types.h>
#include <pcl/sample_consensus/model_types.h>
#include <pcl/segmentation/sac_segmentation.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/filters/conditional_removal.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Quaternion.h>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <pcl/filters/voxel_grid.h>

#include <opencv2/opencv.hpp>
#include <sensor_msgs/msg/camera_info.hpp>
#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/msg/image.hpp>

#include <pcl_filter_msgs/msg/color_filter.hpp>
#include <pcl_filter_msgs/msg/shape_filter.hpp>

#include <string>

#define RED 1
#define GREEN 2
#define BLUE 3
#define PURPLE 4

#define SPHERE 1
#define CYLINDER 2

typedef pcl::PointCloud<pcl::PointXYZ> PointCloud;
typedef pcl::PointCloud<pcl::PointXYZRGB> PointCloudRGB;
typedef pcl::PointXYZ PointT;

struct ColorRange
{
  int rMax;
  int rMin;
  int bMax;
  int bMin;
  int gMax;
  int gMin;
};

class ObjectDetection : public rclcpp::Node
{
public:
  ObjectDetection() : Node("object_detection")
  {
    pub_green_sphere = this->create_publisher<sensor_msgs::msg::PointCloud2>("/green_sphere", 1);
    pub_red_sphere = this->create_publisher<sensor_msgs::msg::PointCloud2>("/red_sphere", 1);
    pub_blue_sphere = this->create_publisher<sensor_msgs::msg::PointCloud2>("/blue_sphere", 1);
    pub_purple_sphere = this->create_publisher<sensor_msgs::msg::PointCloud2>("/purple_sphere", 1);
    pub_green_cylinder = this->create_publisher<sensor_msgs::msg::PointCloud2>("/green_cylinder", 1);
    pub_red_cylinder = this->create_publisher<sensor_msgs::msg::PointCloud2>("/red_cylinder", 1);
    pub_blue_cylinder = this->create_publisher<sensor_msgs::msg::PointCloud2>("/blue_cylinder", 1);
    pub_purple_cylinder = this->create_publisher<sensor_msgs::msg::PointCloud2>("/purple_cylinder", 1);

    pub_blue = this->create_publisher<sensor_msgs::msg::PointCloud2>("/blue_filter", 1);
    pub_red = this->create_publisher<sensor_msgs::msg::PointCloud2>("/red_filter", 1);
    pub_green = this->create_publisher<sensor_msgs::msg::PointCloud2>("/green_filter", 1);
    pub_purple = this->create_publisher<sensor_msgs::msg::PointCloud2>("/purple_filter", 1);

    image_pub_blue = this->create_publisher<sensor_msgs::msg::Image>("blue_filtered_image", 1);
    image_pub_green = this->create_publisher<sensor_msgs::msg::Image>("green_filtered_image", 1);
    image_pub_red = this->create_publisher<sensor_msgs::msg::Image>("red_filtered_image", 1);
    image_pub_purple = this->create_publisher<sensor_msgs::msg::Image>("purple_filtered_image", 1);

    image_pub_green_sphere = this->create_publisher<sensor_msgs::msg::Image>("/green_sphere_image", 1);
    image_pub_red_sphere = this->create_publisher<sensor_msgs::msg::Image>("/red_sphere_image", 1);
    image_pub_blue_sphere = this->create_publisher<sensor_msgs::msg::Image>("/blue_sphere_image", 1);
    image_pub_purple_sphere = this->create_publisher<sensor_msgs::msg::Image>("/purple_sphere_image", 1);
    image_pub_green_cylinder = this->create_publisher<sensor_msgs::msg::Image>("/green_cylinder_image", 1);
    image_pub_red_cylinder = this->create_publisher<sensor_msgs::msg::Image>("/red_cylinder_image", 1);
    image_pub_blue_cylinder = this->create_publisher<sensor_msgs::msg::Image>("/blue_cylinder_image", 1);
    image_pub_purple_cylinder = this->create_publisher<sensor_msgs::msg::Image>("/purple_cylinder_image", 1);

    sub_color_filter = this->create_subscription<pcl_filter_msgs::msg::ColorFilter>(
      "/start_color_filter", 1, 
      std::bind(&ObjectDetection::call_color_filter, this, std::placeholders::_1));
    
    sub_shape_filter = this->create_subscription<pcl_filter_msgs::msg::ShapeFilter>(
      "/start_shape_filter", 1, 
      std::bind(&ObjectDetection::call_shape_filter, this, std::placeholders::_1));

    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
  }

  void call_color_filter(const pcl_filter_msgs::msg::ColorFilter::SharedPtr msg)
  {      
    if(msg->status == true){
      // start color filter
      switch(msg->color){
        case RED:
          assign_color_range(red_range, msg->rmax, msg->rmin, msg->gmax, msg->gmin, msg->bmax, msg->bmin);
          sub_red = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            "/base_camera/points", 1, 
            std::bind(&ObjectDetection::redfilter_callback, this, std::placeholders::_1));
          break;
        case GREEN:
          assign_color_range(green_range, msg->rmax, msg->rmin, msg->gmax, msg->gmin, msg->bmax, msg->bmin);
          sub_green = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            "/base_camera/points", 1, 
            std::bind(&ObjectDetection::greenfilter_callback, this, std::placeholders::_1));
          break;
        case BLUE:
          assign_color_range(blue_range, msg->rmax, msg->rmin, msg->gmax, msg->gmin, msg->bmax, msg->bmin);
          sub_blue = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            "/base_camera/points", 1, 
            std::bind(&ObjectDetection::bluefilter_callback, this, std::placeholders::_1));
          break;
        case PURPLE:
          assign_color_range(purple_range, msg->rmax, msg->rmin, msg->gmax, msg->gmin, msg->bmax, msg->bmin);
          sub_purple = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            "/base_camera/points", 1, 
            std::bind(&ObjectDetection::purplefilter_callback, this, std::placeholders::_1));
          break;
      }
    }
    else{
      // stop color filter
      switch(msg->color){
        case BLUE:
          sub_blue.reset();
          // Clear the point cloud topic
          {
            sensor_msgs::msg::PointCloud2 empty_msg;
            empty_msg.header.stamp = this->get_clock()->now();
            empty_msg.header.frame_id = "base_camera_optical_link";
            empty_msg.height = 0;
            empty_msg.width = 0;
            pub_blue->publish(empty_msg);
          }
          // Also clear the image topic with a black image
          {
            cv::Mat black_image = cv::Mat::zeros(480, 640, CV_8UC3);
            std_msgs::msg::Header header;
            header.frame_id = "base_camera_optical_link";
            header.stamp = this->get_clock()->now();
            sensor_msgs::msg::Image::SharedPtr black_image_msg = cv_bridge::CvImage(header, "rgb8", black_image).toImageMsg();
            image_pub_blue->publish(*black_image_msg);
          }
          break;
        case RED:
          sub_red.reset();
          // Clear the point cloud topic
          {
            sensor_msgs::msg::PointCloud2 empty_msg;
            empty_msg.header.stamp = this->get_clock()->now();
            empty_msg.header.frame_id = "base_camera_optical_link";
            empty_msg.height = 0;
            empty_msg.width = 0;
            pub_red->publish(empty_msg);
          }
          // Also clear the image topic with a black image
          {
            cv::Mat black_image = cv::Mat::zeros(480, 640, CV_8UC3);
            std_msgs::msg::Header header;
            header.frame_id = "base_camera_optical_link";
            header.stamp = this->get_clock()->now();
            sensor_msgs::msg::Image::SharedPtr black_image_msg = cv_bridge::CvImage(header, "rgb8", black_image).toImageMsg();
            image_pub_red->publish(*black_image_msg);
          }
          break;
        case GREEN:
          sub_green.reset();
          // Clear the point cloud topic
          {
            sensor_msgs::msg::PointCloud2 empty_msg;
            empty_msg.header.stamp = this->get_clock()->now();
            empty_msg.header.frame_id = "base_camera_optical_link";
            empty_msg.height = 0;
            empty_msg.width = 0;
            pub_green->publish(empty_msg);
          }
          // Also clear the image topic with a black image
          {
            cv::Mat black_image = cv::Mat::zeros(480, 640, CV_8UC3);
            std_msgs::msg::Header header;
            header.frame_id = "base_camera_optical_link";
            header.stamp = this->get_clock()->now();
            sensor_msgs::msg::Image::SharedPtr black_image_msg = cv_bridge::CvImage(header, "rgb8", black_image).toImageMsg();
            image_pub_green->publish(*black_image_msg);
          }
          break;
        case PURPLE:
          sub_purple.reset();
          // Clear the point cloud topic
          {
            sensor_msgs::msg::PointCloud2 empty_msg;
            empty_msg.header.stamp = this->get_clock()->now();
            empty_msg.header.frame_id = "base_camera_optical_link";
            empty_msg.height = 0;
            empty_msg.width = 0;
            pub_purple->publish(empty_msg);
          }
          // Also clear the image topic with a black image
          {
            cv::Mat black_image = cv::Mat::zeros(480, 640, CV_8UC3);
            std_msgs::msg::Header header;
            header.frame_id = "base_camera_optical_link";
            header.stamp = this->get_clock()->now();
            sensor_msgs::msg::Image::SharedPtr black_image_msg = cv_bridge::CvImage(header, "rgb8", black_image).toImageMsg();
            image_pub_purple->publish(*black_image_msg);
          }
          break;
      }
    }
  }

  void call_shape_filter(const pcl_filter_msgs::msg::ShapeFilter::SharedPtr msg)
  {
    if(msg->status == true){
      if(msg->color == RED && msg->shape == SPHERE)
      {
        red_sphere_radius = msg->radius;
        sub_red_sphere = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/red_filter", 1, 
          std::bind(&ObjectDetection::red_sphere_callback, this, std::placeholders::_1));
      }
      else if(msg->color == RED && msg->shape == CYLINDER)
      {
        red_cylinder_radius = msg->radius;
        sub_red_cylinder = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/red_filter", 1, 
          std::bind(&ObjectDetection::red_cylinder_callback, this, std::placeholders::_1));
      }
      else if(msg->color == GREEN && msg->shape == SPHERE)
      {
        green_sphere_radius = msg->radius;
        sub_green_sphere = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/green_filter", 1, 
          std::bind(&ObjectDetection::green_sphere_callback, this, std::placeholders::_1));
      }
      else if(msg->color == GREEN && msg->shape == CYLINDER)
      {
        green_cylinder_radius = msg->radius;
        sub_green_cylinder = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/green_filter", 1, 
          std::bind(&ObjectDetection::green_cylinder_callback, this, std::placeholders::_1));
      }
      else if(msg->color == BLUE && msg->shape == SPHERE)
      {
        blue_sphere_radius = msg->radius;
        sub_blue_sphere = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/blue_filter", 1, 
          std::bind(&ObjectDetection::blue_sphere_callback, this, std::placeholders::_1));
      }
      else if(msg->color == BLUE && msg->shape == CYLINDER)
      {
        blue_cylinder_radius = msg->radius;
        sub_blue_cylinder = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/blue_filter", 1, 
          std::bind(&ObjectDetection::blue_cylinder_callback, this, std::placeholders::_1));
      }
      else if(msg->color == PURPLE && msg->shape == SPHERE)
      {
        purple_sphere_radius = msg->radius;
        sub_purple_sphere = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/purple_filter", 1, 
          std::bind(&ObjectDetection::purple_sphere_callback, this, std::placeholders::_1));
      }
      else if(msg->color == PURPLE && msg->shape == CYLINDER)
      {
        purple_cylinder_radius = msg->radius;
        sub_purple_cylinder = this->create_subscription<sensor_msgs::msg::PointCloud2>(
          "/purple_filter", 1, 
          std::bind(&ObjectDetection::purple_cylinder_callback, this, std::placeholders::_1));
      }
    }
    else{
      if(msg->color == RED && msg->shape == SPHERE)
        sub_red_sphere.reset();
      else if(msg->color == RED && msg->shape == CYLINDER)
        sub_red_cylinder.reset();
      else if(msg->color == GREEN && msg->shape == SPHERE)
        sub_green_sphere.reset();
      else if(msg->color == GREEN && msg->shape == CYLINDER)
        sub_green_cylinder.reset();
      else if(msg->color == BLUE && msg->shape == SPHERE)
        sub_blue_sphere.reset();
      else if(msg->color == BLUE && msg->shape == CYLINDER)
        sub_blue_cylinder.reset();
      else if(msg->color == PURPLE && msg->shape == SPHERE)
        sub_purple_sphere.reset();
      else if(msg->color == PURPLE && msg->shape == CYLINDER)
        sub_purple_cylinder.reset();
    }
  }

  void assign_color_range(ColorRange &color_range, int rMax, int rMin, int gMax, int gMin, int bMax, int bMin){
    color_range.rMax = rMax;
    color_range.rMin = rMin;
    color_range.gMax = gMax;
    color_range.gMin = gMin;
    color_range.bMax = bMax;
    color_range.bMin = bMin;
  }

  void purplefilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond (new pcl::ConditionAnd<pcl::PointXYZRGB> ());
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::LT, purple_range.bMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::GT, purple_range.bMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::LT, purple_range.rMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::GT, purple_range.rMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::LT, purple_range.gMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::GT, purple_range.gMin)));

    // Build the filter
    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition (color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*cloud_color_filtered, output_msg);
    output_msg.header = msg->header;
    pub_purple->publish(output_msg);
    pointcloud_to_rgb_image(cloud_color_filtered, image_pub_purple);
  }

  void bluefilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond (new pcl::ConditionAnd<pcl::PointXYZRGB> ());
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::LT, blue_range.bMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::GT, blue_range.bMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::LT, blue_range.rMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::GT, blue_range.rMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::LT, blue_range.gMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::GT, blue_range.gMin)));

    // Build the filter
    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition (color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*cloud_color_filtered, output_msg);
    output_msg.header = msg->header;
    pub_blue->publish(output_msg);
    pointcloud_to_rgb_image(cloud_color_filtered, image_pub_blue);
  }

  void redfilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond (new pcl::ConditionAnd<pcl::PointXYZRGB> ());
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::LT, red_range.rMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::GT, red_range.rMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::LT, red_range.gMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::GT, red_range.gMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::LT, red_range.bMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::GT, red_range.bMin)));

    // Build the filter
    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition (color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*cloud_color_filtered, output_msg);
    output_msg.header = msg->header;
    pub_red->publish(output_msg);
    pointcloud_to_rgb_image(cloud_color_filtered, image_pub_red);
  }

  void greenfilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond (new pcl::ConditionAnd<pcl::PointXYZRGB> ());
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::LT, green_range.gMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("g", pcl::ComparisonOps::GT, green_range.gMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::LT, green_range.rMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("r", pcl::ComparisonOps::GT, green_range.rMin)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::LT, green_range.bMax)));
    color_cond->addComparison (pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr (new pcl::PackedRGBComparison<pcl::PointXYZRGB> ("b", pcl::ComparisonOps::GT, green_range.bMin)));

    // Build the filter
    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition (color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*cloud_color_filtered, output_msg);
    output_msg.header = msg->header;
    pub_green->publish(output_msg);
    pointcloud_to_rgb_image(cloud_color_filtered, image_pub_green);
  }

  void green_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_sphere(cloud_input, pub_green_sphere, image_pub_green_sphere, "green_sphere", green_sphere_radius);
  }

  void red_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_sphere(cloud_input, pub_red_sphere, image_pub_red_sphere, "red_sphere", red_sphere_radius);
  }

  void blue_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_sphere(cloud_input, pub_blue_sphere, image_pub_blue_sphere, "blue_sphere", blue_sphere_radius);
  }

  void purple_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_sphere(cloud_input, pub_purple_sphere, image_pub_purple_sphere, "purple_sphere", purple_sphere_radius);
  }

  void green_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_cylinder(cloud_input, pub_green_cylinder, image_pub_green_cylinder, "green_cylinder", green_cylinder_radius);
  }

  void red_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_cylinder(cloud_input, pub_red_cylinder, image_pub_red_cylinder, "red_cylinder", red_cylinder_radius);
  }

  void blue_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_cylinder(cloud_input, pub_blue_cylinder, image_pub_blue_cylinder, "blue_cylinder", blue_cylinder_radius);
  }

  void purple_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloud::Ptr cloud_input(new PointCloud);
    pcl::fromROSMsg(*msg, *cloud_input);
    detect_cylinder(cloud_input, pub_purple_cylinder, image_pub_purple_cylinder, "purple_cylinder", purple_cylinder_radius);
  }

  void detect_cylinder(
    const PointCloud::Ptr& cloud,
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub,
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub,
    std::string frame_id,
    float radius)
{
  // ---------- Safety pre-pass ----------
  PointCloud::Ptr cloud_clean(new PointCloud);
  std::vector<int> idx;
  pcl::removeNaNFromPointCloud(*cloud, *cloud_clean, idx);
  if (!cloud_clean || cloud_clean->points.size() < 30) return;

  // ---------- (unchanged core) ----------
  pcl::PassThrough<PointT> pass;
  pcl::NormalEstimation<PointT, pcl::Normal> ne;
  pcl::SACSegmentationFromNormals<PointT, pcl::Normal> seg; 
  pcl::ExtractIndices<PointT> extract;
  pcl::ExtractIndices<pcl::Normal> extract_normals;
  pcl::search::KdTree<PointT>::Ptr tree (new pcl::search::KdTree<PointT> ());

  PointCloud::Ptr cloud_filtered (new PointCloud);
  pcl::PointCloud<pcl::Normal>::Ptr cloud_normals (new pcl::PointCloud<pcl::Normal>);
  PointCloud::Ptr cloud_filtered2 (new PointCloud);
  pcl::PointCloud<pcl::Normal>::Ptr cloud_normals2 (new pcl::PointCloud<pcl::Normal>);
  pcl::ModelCoefficients::Ptr coefficients_plane (new pcl::ModelCoefficients), coefficients_cylinder (new pcl::ModelCoefficients);
  pcl::PointIndices::Ptr inliers_plane (new pcl::PointIndices), inliers_cylinder (new pcl::PointIndices);

  pass.setInputCloud (cloud_clean);
  pass.setFilterFieldName ("z");
  pass.setFilterLimits (0.05, 2.0);
  pass.filter (*cloud_filtered);
  if (cloud_filtered->points.size() < 50) return;

  ne.setSearchMethod (tree);
  ne.setInputCloud (cloud_filtered);
  ne.setKSearch (20);
  ne.compute (*cloud_normals);
  if (cloud_normals->points.size() != cloud_filtered->points.size()) return;

  seg.setOptimizeCoefficients (true);
  seg.setModelType (pcl::SACMODEL_NORMAL_PLANE);
  seg.setNormalDistanceWeight (0.1);
  seg.setMethodType (pcl::SAC_RANSAC);
  seg.setMaxIterations (100);
  seg.setDistanceThreshold (0.05);
  seg.setInputCloud (cloud_filtered);
  seg.setInputNormals (cloud_normals);
  seg.segment (*inliers_plane, *coefficients_plane);

  extract.setInputCloud (cloud_filtered);
  extract.setIndices (inliers_plane);
  extract.setNegative (true);
  extract.filter (*cloud_filtered2);

  extract_normals.setNegative (true);
  extract_normals.setInputCloud (cloud_normals);
  extract_normals.setIndices (inliers_plane);
  extract_normals.filter (*cloud_normals2);

  if (cloud_filtered2->points.size() < 10 || cloud_normals2->points.size() < 10) return;

  seg.setOptimizeCoefficients (true);
  seg.setModelType (pcl::SACMODEL_CYLINDER);
  seg.setMethodType (pcl::SAC_RANSAC);
  seg.setNormalDistanceWeight (0.1);
  seg.setMaxIterations (10000);
  seg.setDistanceThreshold (0.05);
  seg.setRadiusLimits (0.001, radius * 3.0f);
  seg.setInputCloud (cloud_filtered2);
  seg.setInputNormals (cloud_normals2);
  seg.segment (*inliers_cylinder, *coefficients_cylinder);

  if (inliers_cylinder->indices.size() < 5) {
    // fallback: try on cloud_filtered directly
    seg.setInputCloud (cloud_filtered);
    seg.setInputNormals (cloud_normals);
    seg.segment (*inliers_cylinder, *coefficients_cylinder);
    if (inliers_cylinder->indices.size() < 5) return;
  }

  // Validate coefficients before use
  if (coefficients_cylinder->values.size() < 7) return;
  const float detected_radius = coefficients_cylinder->values[6];
  if (!(detected_radius > 0.001f) || !(detected_radius < radius * 5.0f)) return;

  // Extract inliers (choose matching cloud for indices)
  pcl::PointCloud<PointT>::Ptr cylinder_cloud(new pcl::PointCloud<PointT>());
  if (inliers_cylinder->indices.size() <= cloud_filtered2->points.size()) {
    extract.setInputCloud (cloud_filtered2);
  } else {
    extract.setInputCloud (cloud_filtered);
  }
  extract.setIndices (inliers_cylinder);
  extract.setNegative (false);
  extract.filter (*cylinder_cloud);
  if (cylinder_cloud->empty()) return;

  // Publish TF (safe)
  {
    geometry_msgs::msg::TransformStamped t;
    t.header.stamp = this->get_clock()->now();
    t.header.frame_id = "base_camera_optical_link";
    t.child_frame_id = frame_id;
    t.transform.translation.x = coefficients_cylinder->values[0];
    t.transform.translation.y = coefficients_cylinder->values[1];
    t.transform.translation.z = coefficients_cylinder->values[2];
    tf2::Quaternion q; q.setRPY(0,0,0);
    t.transform.rotation.x = q.x();
    t.transform.rotation.y = q.y();
    t.transform.rotation.z = q.z();
    t.transform.rotation.w = q.w();
    tf_broadcaster_->sendTransform(t);
  }

  // Publish cloud
  {
    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*cylinder_cloud, output_msg);
    output_msg.header.stamp = this->get_clock()->now();
    output_msg.header.frame_id = "base_camera_optical_link";
    pub->publish(output_msg);
  }

  // Safe depth image projection (clamped indices; skips bad z)
  {
    const float centre_x = 320.5f, centre_y = 240.5f;
    const float fx = 554.3827128226441f, fy = 554.3827128226441f;
    const int width = 640, height = 480;

    cv::Mat cv_image(height, width, CV_32FC1, cv::Scalar(std::numeric_limits<float>::max()));
    for (const auto& p : cylinder_cloud->points) {
      if (!std::isfinite(p.z) || p.z <= 0.f) continue;
      const float z = p.z * 1000.f;
      const float u = (p.x * 1000.f * fx) / z + centre_x;
      const float v = (p.y * 1000.f * fy) / z + centre_y;
      const int px = std::clamp(static_cast<int>(std::lround(u)), 0, width  - 1);
      const int py = std::clamp(static_cast<int>(std::lround(v)), 0, height - 1);
      cv_image.at<float>(py, px) = z;
    }

    std_msgs::msg::Header header;
    header.frame_id = "base_camera_optical_link";
    header.stamp = this->get_clock()->now();
    auto out_img = cv_bridge::CvImage(header, "32FC1", cv_image).toImageMsg();
    image_pub->publish(*out_img);
  }
}

void detect_sphere(
    const PointCloud::Ptr& cloud,
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub,
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub,
    std::string frame_id,
    float radius)
{
  // ---------- Safety pre-pass ----------
  PointCloud::Ptr cloud_clean(new PointCloud);
  std::vector<int> idx;
  pcl::removeNaNFromPointCloud(*cloud, *cloud_clean, idx);
  if (!cloud_clean || cloud_clean->points.size() < 50) return;

  // ---------- (unchanged core) ----------
  pcl::PassThrough<PointT> pass;
  pcl::NormalEstimation<PointT, pcl::Normal> ne;
  pcl::SACSegmentationFromNormals<PointT, pcl::Normal> seg; 
  pcl::ExtractIndices<PointT> extract;
  pcl::ExtractIndices<pcl::Normal> extract_normals;
  pcl::search::KdTree<PointT>::Ptr tree (new pcl::search::KdTree<PointT> ());

  PointCloud::Ptr cloud_filtered (new PointCloud);
  pcl::PointCloud<pcl::Normal>::Ptr cloud_normals (new pcl::PointCloud<pcl::Normal>);
  PointCloud::Ptr cloud_filtered2 (new PointCloud);
  pcl::PointCloud<pcl::Normal>::Ptr cloud_normals2 (new pcl::PointCloud<pcl::Normal>);
  pcl::ModelCoefficients::Ptr coefficients_plane (new pcl::ModelCoefficients), coefficients_sphere (new pcl::ModelCoefficients);
  pcl::PointIndices::Ptr inliers_plane (new pcl::PointIndices), inliers_sphere (new pcl::PointIndices);

  pass.setInputCloud (cloud_clean);
  pass.setFilterFieldName ("z");
  pass.setFilterLimits (0.05, 2.0);
  pass.filter (*cloud_filtered);
  if (cloud_filtered->points.size() < 100) return;

  ne.setSearchMethod (tree);
  ne.setInputCloud (cloud_filtered);
  ne.setKSearch (30);
  ne.compute (*cloud_normals);
  if (cloud_normals->points.size() != cloud_filtered->points.size()) return;

  seg.setOptimizeCoefficients (true);
  seg.setModelType (pcl::SACMODEL_NORMAL_PLANE);
  seg.setNormalDistanceWeight (0.1);
  seg.setMethodType (pcl::SAC_RANSAC);
  seg.setMaxIterations (100);
  seg.setDistanceThreshold (0.05);
  seg.setInputCloud (cloud_filtered);
  seg.setInputNormals (cloud_normals);
  seg.segment (*inliers_plane, *coefficients_plane);

  extract.setInputCloud (cloud_filtered);
  extract.setIndices (inliers_plane);
  extract.setNegative (true);
  extract.filter (*cloud_filtered2);

  extract_normals.setNegative (true);
  extract_normals.setInputCloud (cloud_normals);
  extract_normals.setIndices (inliers_plane);
  extract_normals.filter (*cloud_normals2);

  if (cloud_filtered2->points.size() < 20 || cloud_normals2->points.size() < 20) return;

  seg.setOptimizeCoefficients (true);
  seg.setModelType (pcl::SACMODEL_NORMAL_SPHERE);
  seg.setMethodType (pcl::SAC_RANSAC);
  seg.setNormalDistanceWeight (0.1);
  seg.setMaxIterations (10000);
  seg.setDistanceThreshold (0.05);
  seg.setRadiusLimits (0.001f, radius * 3.0f);
  seg.setInputCloud (cloud_filtered2);
  seg.setInputNormals (cloud_normals2);
  seg.segment (*inliers_sphere, *coefficients_sphere);

  if (inliers_sphere->indices.size() < 10) {
    // fallback: try on cloud_filtered directly
    seg.setInputCloud (cloud_filtered);
    seg.setInputNormals (cloud_normals);
    seg.segment (*inliers_sphere, *coefficients_sphere);
    if (inliers_sphere->indices.size() < 10) return;
  }

  // Validate coefficients before use
  if (coefficients_sphere->values.size() < 4) return;
  const float detected_radius = coefficients_sphere->values[3];
  if (!(detected_radius > 0.001f) || !(detected_radius < radius * 5.0f)) return;

  // Extract inliers (choose matching cloud for indices)
  pcl::PointCloud<PointT>::Ptr sphere_cloud(new pcl::PointCloud<PointT>());
  if (inliers_sphere->indices.size() <= cloud_filtered2->points.size()) {
    extract.setInputCloud (cloud_filtered2);
  } else {
    extract.setInputCloud (cloud_filtered);
  }
  extract.setIndices (inliers_sphere);
  extract.setNegative (false);
  extract.filter (*sphere_cloud);
  if (sphere_cloud->empty()) return;

  // Publish TF (safe)
  {
    geometry_msgs::msg::TransformStamped t;
    t.header.stamp = this->get_clock()->now();
    t.header.frame_id = "base_camera_optical_link";
    t.child_frame_id = frame_id;
    t.transform.translation.x = coefficients_sphere->values[0];
    t.transform.translation.y = coefficients_sphere->values[1];
    t.transform.translation.z = coefficients_sphere->values[2];
    tf2::Quaternion q; q.setRPY(0,0,0);
    t.transform.rotation.x = q.x();
    t.transform.rotation.y = q.y();
    t.transform.rotation.z = q.z();
    t.transform.rotation.w = q.w();
    tf_broadcaster_->sendTransform(t);
  }

  // Publish cloud
  {
    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*sphere_cloud, output_msg);
    output_msg.header.stamp = this->get_clock()->now();
    output_msg.header.frame_id = "base_camera_optical_link";
    pub->publish(output_msg);
  }

  // Safe depth image projection (clamped indices; skips bad z)
  {
    const float centre_x = 320.5f, centre_y = 240.5f;
    const float fx = 554.3827128226441f, fy = 554.3827128226441f;
    const int width = 640, height = 480;

    cv::Mat cv_image(height, width, CV_32FC1, cv::Scalar(std::numeric_limits<float>::max()));
    for (const auto& p : sphere_cloud->points) {
      if (!std::isfinite(p.z) || p.z <= 0.f) continue;
      const float z = p.z * 1000.f;
      const float u = (p.x * 1000.f * fx) / z + centre_x;
      const float v = (p.y * 1000.f * fy) / z + centre_y;
      const int px = std::clamp(static_cast<int>(std::lround(u)), 0, width  - 1);
      const int py = std::clamp(static_cast<int>(std::lround(v)), 0, height - 1);
      cv_image.at<float>(py, px) = z;
    }

    std_msgs::msg::Header header;
    header.frame_id = "base_camera_optical_link";
    header.stamp = this->get_clock()->now();
    auto out_img = cv_bridge::CvImage(header, "32FC1", cv_image).toImageMsg();
    image_pub->publish(*out_img);
  }
}


  void pointcloud_to_depth_image(const PointCloud::Ptr& msg, rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub)
{
  float centre_x = 320.5;
  float centre_y = 240.5;
  float focal_x = 554.3827128226441;
  float focal_y = 554.3827128226441;
  int height = 480;
  int width = 640;

  cv::Mat cv_image = cv::Mat(height, width, CV_32FC1, cv::Scalar(std::numeric_limits<float>::max()));

  for (int i=0; i<msg->points.size();i++){
    if (msg->points[i].z == msg->points[i].z){
      float z = msg->points[i].z*1000.0;
      float u = (msg->points[i].x*1000.0*focal_x) / z;
      float v = (msg->points[i].y*1000.0*focal_y) / z;
      int pixel_pos_x = (int)(u + centre_x);
      int pixel_pos_y = (int)(v + centre_y);

      if (pixel_pos_x > (width-1)){
        pixel_pos_x = width -1;
      }
      if (pixel_pos_y > (height-1)){
        pixel_pos_y = height-1;
      }
      cv_image.at<float>(pixel_pos_y,pixel_pos_x) = z;
    }       
  }

  std_msgs::msg::Header header;
  header.frame_id = "base_camera_optical_link";
  header.stamp = this->get_clock()->now();
  sensor_msgs::msg::Image::SharedPtr output_image = cv_bridge::CvImage(header, "32FC1", cv_image).toImageMsg();
  pub->publish(*output_image);
}

  void pointcloud_to_rgb_image(const PointCloudRGB::Ptr& msg, rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub)
  {
    float centre_x = 320.5;
    float centre_y = 240.5;
    float focal_x = 554.3827128226441;
    float focal_y = 554.3827128226441;
    int height = 480;
    int width = 640;

    cv::Mat cv_image = cv::Mat(height, width, CV_8UC3);

    for (int i=0; i<msg->points.size();i++){
      if (msg->points[i].z == msg->points[i].z){
        float z = msg->points[i].z*1000.0;
        float u = (msg->points[i].x*1000.0*focal_x) / z;
        float v = (msg->points[i].y*1000.0*focal_y) / z;
        int pixel_pos_x = (int)(u + centre_x);
        int pixel_pos_y = (int)(v + centre_y);

        int r = msg->points[i].r;
        int g = msg->points[i].g;
        int b = msg->points[i].b;

        if (pixel_pos_x > (width-1)){
          pixel_pos_x = width -1;
        }
        if (pixel_pos_y > (height-1)){
          pixel_pos_y = height-1;
        }

        cv_image.at<cv::Vec3b>(pixel_pos_y,pixel_pos_x) = cv::Vec3b(b, g, r);
      }       
    }

    std_msgs::msg::Header header;
    header.frame_id = "base_camera_optical_link";
    header.stamp = this->get_clock()->now();
    sensor_msgs::msg::Image::SharedPtr output_image = cv_bridge::CvImage(header, "bgr8", cv_image).toImageMsg();
    pub->publish(*output_image);
  }

private:
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_blue_sphere;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_red_sphere;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_green_sphere;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_purple_sphere;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_red_cylinder;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_green_cylinder;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_blue_cylinder;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_purple_cylinder;

  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_blue;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_red;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_green;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_purple;

  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_blue;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_red;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_green;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_purple;

  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_blue_sphere;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_red_sphere;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_green_sphere;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_purple_sphere;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_red_cylinder;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_green_cylinder;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_blue_cylinder;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_purple_cylinder;

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_red_sphere;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_green_sphere;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_blue_sphere;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_purple_sphere;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_red_cylinder;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_green_cylinder;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_blue_cylinder;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_purple_cylinder;

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_blue;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_red;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_green;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_purple;

  rclcpp::Subscription<pcl_filter_msgs::msg::ColorFilter>::SharedPtr sub_color_filter;
  rclcpp::Subscription<pcl_filter_msgs::msg::ShapeFilter>::SharedPtr sub_shape_filter;

  std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

  ColorRange red_range;
  ColorRange green_range;
  ColorRange blue_range;
  ColorRange purple_range;

  float red_sphere_radius;
  float red_cylinder_radius;
  float green_sphere_radius;
  float green_cylinder_radius;
  float blue_sphere_radius;
  float blue_cylinder_radius;
  float purple_sphere_radius;
  float purple_cylinder_radius;

  bool red_filter_success;
  bool green_filter_success;
  bool blue_filter_success;
  bool purple_filter_success;

  bool red_sphere_success;
  bool red_cylinder_success;
  bool green_sphere_success;
  bool green_cylinder_success;
  bool blue_sphere_success;
  bool blue_cylinder_success;
  bool purple_sphere_success;
  bool purple_cylinder_success;
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ObjectDetection>());
  rclcpp::shutdown();
  return 0;
}
