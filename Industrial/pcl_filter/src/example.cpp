#include <rclcpp/rclcpp.hpp>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_types.h>
#include <pcl/ModelCoefficients.h>
#include <pcl/filters/extract_indices.h>
#include <pcl/filters/passthrough.h>
#include <pcl/features/normal_3d.h>
#include <pcl/sample_consensus/method_types.h>
#include <pcl/sample_consensus/model_types.h>
#include <pcl/segmentation/sac_segmentation.h>
#include <pcl/filters/conditional_removal.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Quaternion.h>
#include <geometry_msgs/msg/transform_stamped.hpp>

#include <opencv2/opencv.hpp>
#include <sensor_msgs/msg/camera_info.hpp>
#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/msg/image.hpp>

typedef pcl::PointCloud<pcl::PointXYZ> PointCloud;
typedef pcl::PointCloud<pcl::PointXYZRGB> PointCloudRGB;
typedef pcl::PointXYZ PointT;

class ObjectDetection : public rclcpp::Node
{
public:
  ObjectDetection() : Node("object_detection"), tf_broadcaster_(this)
  {
    // Publishers for spheres
    pub_green_sphere_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/green_sphere", 1);
    pub_red_sphere_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/red_sphere", 1);
    pub_blue_sphere_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/blue_sphere", 1);
    pub_yellow_sphere_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/yellow_sphere", 1);
    
    // Publishers for cylinders
    pub_green_cylinder_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/green_cylinder", 1);
    pub_red_cylinder_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/red_cylinder", 1);
    pub_blue_cylinder_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/blue_cylinder", 1);
    pub_yellow_cylinder_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/yellow_cylinder", 1);

    // Publishers for filtered clouds
    pub_blue_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/blue_filter", 1);
    pub_red_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/red_filter", 1);
    pub_green_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/green_filter", 1);
    pub_yellow_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/yellow_filter", 1);

    // Publishers for filtered images
    image_pub_blue_ = this->create_publisher<sensor_msgs::msg::Image>("blue_filtered_image", 1);
    image_pub_green_ = this->create_publisher<sensor_msgs::msg::Image>("green_filtered_image", 1);
    image_pub_red_ = this->create_publisher<sensor_msgs::msg::Image>("red_filtered_image", 1);
    image_pub_yellow_ = this->create_publisher<sensor_msgs::msg::Image>("yellow_filtered_image", 1);

    // Publishers for object images
    image_pub_green_sphere_ = this->create_publisher<sensor_msgs::msg::Image>("/green_sphere_image", 1);
    image_pub_red_sphere_ = this->create_publisher<sensor_msgs::msg::Image>("/red_sphere_image", 1);
    image_pub_blue_sphere_ = this->create_publisher<sensor_msgs::msg::Image>("/blue_sphere_image", 1);
    image_pub_yellow_sphere_ = this->create_publisher<sensor_msgs::msg::Image>("/yellow_sphere_image", 1);
    image_pub_green_cylinder_ = this->create_publisher<sensor_msgs::msg::Image>("/green_cylinder_image", 1);
    image_pub_red_cylinder_ = this->create_publisher<sensor_msgs::msg::Image>("/red_cylinder_image", 1);
    image_pub_blue_cylinder_ = this->create_publisher<sensor_msgs::msg::Image>("/blue_cylinder_image", 1);
    image_pub_yellow_cylinder_ = this->create_publisher<sensor_msgs::msg::Image>("/yellow_cylinder_image", 1);

    // Subscribers for sphere detection
    sub_green_sphere_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/green_filter", 1, std::bind(&ObjectDetection::green_sphere_callback, this, std::placeholders::_1));
    sub_red_sphere_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/red_filter", 1, std::bind(&ObjectDetection::red_sphere_callback, this, std::placeholders::_1));
    sub_blue_sphere_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/blue_filter", 1, std::bind(&ObjectDetection::blue_sphere_callback, this, std::placeholders::_1));
    sub_yellow_sphere_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/yellow_filter", 1, std::bind(&ObjectDetection::yellow_sphere_callback, this, std::placeholders::_1));

    // Subscribers for cylinder detection
    sub_green_cylinder_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/green_filter", 1, std::bind(&ObjectDetection::green_cylinder_callback, this, std::placeholders::_1));
    sub_red_cylinder_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/red_filter", 1, std::bind(&ObjectDetection::red_cylinder_callback, this, std::placeholders::_1));
    sub_blue_cylinder_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/blue_filter", 1, std::bind(&ObjectDetection::blue_cylinder_callback, this, std::placeholders::_1));
    sub_yellow_cylinder_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/yellow_filter", 1, std::bind(&ObjectDetection::yellow_cylinder_callback, this, std::placeholders::_1));

    // Subscribers for color filtering
    sub_blue_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/kinect_camera_fixed/depth/points", 1, std::bind(&ObjectDetection::bluefilter_callback, this, std::placeholders::_1));
    sub_red_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/kinect_camera_fixed/depth/points", 1, std::bind(&ObjectDetection::redfilter_callback, this, std::placeholders::_1));
    sub_green_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/kinect_camera_fixed/depth/points", 1, std::bind(&ObjectDetection::greenfilter_callback, this, std::placeholders::_1));
    sub_yellow_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/kinect_camera_fixed/depth/points", 1, std::bind(&ObjectDetection::yellowfilter_callback, this, std::placeholders::_1));
  }

  void yellowfilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    int bMax = 50;
    int rMax = 255;
    int rMin = 90;
    int gMax = 255;
    int gMin = 90;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond(new pcl::ConditionAnd<pcl::PointXYZRGB>());
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("b", pcl::ComparisonOps::LT, bMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("r", pcl::ComparisonOps::LT, rMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("r", pcl::ComparisonOps::GT, rMin)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("g", pcl::ComparisonOps::LT, gMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("g", pcl::ComparisonOps::GT, gMin)));

    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition(color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(*cloud_color_filtered, output);
    pub_yellow_->publish(output);
  }

  void bluefilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    int bMax = 255;
    int bMin = 90;
    int rMax = 50;
    int gMax = 50;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond(new pcl::ConditionAnd<pcl::PointXYZRGB>());
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("b", pcl::ComparisonOps::LT, bMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("b", pcl::ComparisonOps::GT, bMin)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("r", pcl::ComparisonOps::LT, rMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("g", pcl::ComparisonOps::LT, gMax)));

    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition(color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(*cloud_color_filtered, output);
    pub_blue_->publish(output);
  }

  void redfilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    int rMax = 255;
    int rMin = 90;
    int gMax = 50;
    int bMax = 50;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond(new pcl::ConditionAnd<pcl::PointXYZRGB>());
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("r", pcl::ComparisonOps::LT, rMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("r", pcl::ComparisonOps::GT, rMin)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("g", pcl::ComparisonOps::LT, gMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("b", pcl::ComparisonOps::LT, bMax)));

    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition(color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(*cloud_color_filtered, output);
    pub_red_->publish(output);
  }

  void greenfilter_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    PointCloudRGB::Ptr cloud_input(new PointCloudRGB);
    PointCloudRGB::Ptr cloud_color_filtered(new PointCloudRGB);
    
    pcl::fromROSMsg(*msg, *cloud_input);

    pcl::ConditionalRemoval<pcl::PointXYZRGB> color_filter;

    int gMax = 255;
    int gMin = 90;
    int rMax = 50;
    int bMax = 50;

    pcl::ConditionAnd<pcl::PointXYZRGB>::Ptr color_cond(new pcl::ConditionAnd<pcl::PointXYZRGB>());
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("g", pcl::ComparisonOps::LT, gMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("g", pcl::ComparisonOps::GT, gMin)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("r", pcl::ComparisonOps::LT, rMax)));
    color_cond->addComparison(pcl::PackedRGBComparison<pcl::PointXYZRGB>::Ptr(
      new pcl::PackedRGBComparison<pcl::PointXYZRGB>("b", pcl::ComparisonOps::LT, bMax)));

    color_filter.setInputCloud(cloud_input);
    color_filter.setCondition(color_cond);
    color_filter.filter(*cloud_color_filtered);

    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(*cloud_color_filtered, output);
    pub_green_->publish(output);
  }

  void green_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_sphere(msg, pub_green_sphere_, image_pub_green_sphere_, "green_sphere", 0.035);
  }

  void red_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_sphere(msg, pub_red_sphere_, image_pub_red_sphere_, "red_sphere", 0.035);
  }

  void blue_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_sphere(msg, pub_blue_sphere_, image_pub_blue_sphere_, "blue_sphere", 0.035);
  }

  void yellow_sphere_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_sphere(msg, pub_yellow_sphere_, image_pub_yellow_sphere_, "yellow_sphere", 0.045);
  }

  void green_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_cylinder(msg, pub_green_cylinder_, image_pub_green_cylinder_, "green_cylinder", 0.035);
  }

  void red_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_cylinder(msg, pub_red_cylinder_, image_pub_red_cylinder_, "red_cylinder", 0.025);
  }

  void blue_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_cylinder(msg, pub_blue_cylinder_, image_pub_blue_cylinder_, "blue_cylinder", 0.045);
  }

  void yellow_cylinder_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    detect_cylinder(msg, pub_yellow_cylinder_, image_pub_yellow_cylinder_, "yellow_cylinder", 0.025);
  }

  void detect_cylinder(const sensor_msgs::msg::PointCloud2::SharedPtr cloud_msg, 
                      rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub,
                      rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub,
                      std::string frame_id, float radius)
  {
    PointCloud::Ptr cloud(new PointCloud);
    pcl::fromROSMsg(*cloud_msg, *cloud);

    // All the objects needed
    pcl::PassThrough<PointT> pass;
    pcl::NormalEstimation<PointT, pcl::Normal> ne;
    pcl::SACSegmentationFromNormals<PointT, pcl::Normal> seg;
    pcl::ExtractIndices<PointT> extract;
    pcl::ExtractIndices<pcl::Normal> extract_normals;
    pcl::search::KdTree<PointT>::Ptr tree(new pcl::search::KdTree<PointT>());

    // Datasets
    PointCloud::Ptr cloud_filtered(new PointCloud);
    pcl::PointCloud<pcl::Normal>::Ptr cloud_normals(new pcl::PointCloud<pcl::Normal>);
    PointCloud::Ptr cloud_filtered2(new PointCloud);
    pcl::PointCloud<pcl::Normal>::Ptr cloud_normals2(new pcl::PointCloud<pcl::Normal>);
    pcl::ModelCoefficients::Ptr coefficients_plane(new pcl::ModelCoefficients);
    pcl::ModelCoefficients::Ptr coefficients_cylinder(new pcl::ModelCoefficients);
    pcl::PointIndices::Ptr inliers_plane(new pcl::PointIndices);
    pcl::PointIndices::Ptr inliers_cylinder(new pcl::PointIndices);

    // Build a passthrough filter to remove spurious NaNs
    pass.setInputCloud(cloud);
    pass.setFilterFieldName("z");
    pass.setFilterLimits(0, 1);
    pass.filter(*cloud_filtered);

    if (cloud_filtered->points.size() < 1000)
      return;

    // Estimate point normals
    ne.setSearchMethod(tree);
    ne.setInputCloud(cloud_filtered);
    ne.setKSearch(50);
    ne.compute(*cloud_normals);

    // Create the segmentation object for the planar model and set all the parameters
    seg.setOptimizeCoefficients(true);
    seg.setModelType(pcl::SACMODEL_NORMAL_PLANE);
    seg.setNormalDistanceWeight(0.1);
    seg.setMethodType(pcl::SAC_RANSAC);
    seg.setMaxIterations(100);
    seg.setDistanceThreshold(0.03);
    seg.setInputCloud(cloud_filtered);
    seg.setInputNormals(cloud_normals);
    seg.segment(*inliers_plane, *coefficients_plane);

    // Extract the planar inliers from the input cloud
    extract.setInputCloud(cloud_filtered);
    extract.setIndices(inliers_plane);
    extract.setNegative(false);

    // Remove the planar inliers, extract the rest
    extract.setNegative(true);
    extract.filter(*cloud_filtered2);
    extract_normals.setNegative(true);
    extract_normals.setInputCloud(cloud_normals);
    extract_normals.setIndices(inliers_plane);
    extract_normals.filter(*cloud_normals2);

    if (cloud_filtered2->points.size() < 1000)
      return;

    // Create the segmentation object for cylinder segmentation and set all the parameters
    seg.setOptimizeCoefficients(true);
    seg.setModelType(pcl::SACMODEL_CYLINDER);
    seg.setMethodType(pcl::SAC_RANSAC);
    seg.setNormalDistanceWeight(0.1);
    seg.setMaxIterations(10000);
    seg.setDistanceThreshold(0.05);
    seg.setRadiusLimits(0, radius);
    seg.setInputCloud(cloud_filtered2);
    seg.setInputNormals(cloud_normals2);

    // Obtain the cylinder inliers and coefficients
    seg.segment(*inliers_cylinder, *coefficients_cylinder);

    // Broadcast transform
    geometry_msgs::msg::TransformStamped transform_stamped;
    transform_stamped.header.stamp = this->now();
    transform_stamped.header.frame_id = cloud_msg->header.frame_id;
    transform_stamped.child_frame_id = frame_id;
    transform_stamped.transform.translation.x = coefficients_cylinder->values[0];
    transform_stamped.transform.translation.y = coefficients_cylinder->values[1];
    transform_stamped.transform.translation.z = coefficients_cylinder->values[2];
    tf2::Quaternion q;
    q.setRPY(0, 0, 0);
    transform_stamped.transform.rotation.x = q.x();
    transform_stamped.transform.rotation.y = q.y();
    transform_stamped.transform.rotation.z = q.z();
    transform_stamped.transform.rotation.w = q.w();
    tf_broadcaster_.sendTransform(transform_stamped);

    // Write the cylinder inliers to disk
    extract.setInputCloud(cloud_filtered2);
    extract.setIndices(inliers_cylinder);
    extract.setNegative(false);
    PointCloud::Ptr cloud_cylinder(new PointCloud());
    extract.filter(*cloud_cylinder);

    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(*cloud_cylinder, output);
    pub->publish(output);
    pointcloud_to_depth_image(cloud_cylinder, image_pub);
  }

  void detect_sphere(const sensor_msgs::msg::PointCloud2::SharedPtr cloud_msg,
                    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub,
                    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub,
                    std::string frame_id, float radius)
  {
    PointCloud::Ptr cloud(new PointCloud);
    pcl::fromROSMsg(*cloud_msg, *cloud);

    // All the objects needed
    pcl::PassThrough<PointT> pass;
    pcl::NormalEstimation<PointT, pcl::Normal> ne;
    pcl::SACSegmentationFromNormals<PointT, pcl::Normal> seg;
    pcl::ExtractIndices<PointT> extract;
    pcl::ExtractIndices<pcl::Normal> extract_normals;
    pcl::search::KdTree<PointT>::Ptr tree(new pcl::search::KdTree<PointT>());

    // Datasets
    PointCloud::Ptr cloud_filtered(new PointCloud);
    pcl::PointCloud<pcl::Normal>::Ptr cloud_normals(new pcl::PointCloud<pcl::Normal>);
    PointCloud::Ptr cloud_filtered2(new PointCloud);
    pcl::PointCloud<pcl::Normal>::Ptr cloud_normals2(new pcl::PointCloud<pcl::Normal>);
    pcl::ModelCoefficients::Ptr coefficients_plane(new pcl::ModelCoefficients);
    pcl::ModelCoefficients::Ptr coefficients_sphere(new pcl::ModelCoefficients);
    pcl::PointIndices::Ptr inliers_plane(new pcl::PointIndices);
    pcl::PointIndices::Ptr inliers_sphere(new pcl::PointIndices);

    // Build a passthrough filter to remove spurious NaNs
    pass.setInputCloud(cloud);
    pass.setFilterFieldName("z");
    pass.setFilterLimits(0, 1);
    pass.filter(*cloud_filtered);

    if (cloud_filtered->points.size() < 1000)
      return;

    // Estimate point normals
    ne.setSearchMethod(tree);
    ne.setInputCloud(cloud_filtered);
    ne.setKSearch(50);
    ne.compute(*cloud_normals);

    // Create the segmentation object for the planar model and set all the parameters
    seg.setOptimizeCoefficients(true);
    seg.setModelType(pcl::SACMODEL_NORMAL_PLANE);
    seg.setNormalDistanceWeight(0.1);
    seg.setMethodType(pcl::SAC_RANSAC);
    seg.setMaxIterations(100);
    seg.setDistanceThreshold(0.03);
    seg.setInputCloud(cloud_filtered);
    seg.setInputNormals(cloud_normals);
    seg.segment(*inliers_plane, *coefficients_plane);

    // Extract the planar inliers from the input cloud
    extract.setInputCloud(cloud_filtered);
    extract.setIndices(inliers_plane);
    extract.setNegative(false);

    // Remove the planar inliers, extract the rest
    extract.setNegative(true);
    extract.filter(*cloud_filtered2);
    extract_normals.setNegative(true);
    extract_normals.setInputCloud(cloud_normals);
    extract_normals.setIndices(inliers_plane);
    extract_normals.filter(*cloud_normals2);

    if (cloud_filtered2->points.size() < 1000)
      return;

    // Create the segmentation object for sphere segmentation and set all the parameters
    seg.setOptimizeCoefficients(true);
    seg.setModelType(pcl::SACMODEL_NORMAL_SPHERE);
    seg.setMethodType(pcl::SAC_RANSAC);
    seg.setNormalDistanceWeight(0.1);
    seg.setMaxIterations(10000);
    seg.setDistanceThreshold(0.05);
    seg.setRadiusLimits(0, radius);
    seg.setInputCloud(cloud_filtered2);
    seg.setInputNormals(cloud_normals2);

    // Obtain the sphere inliers and coefficients
    seg.segment(*inliers_sphere, *coefficients_sphere);

    // Broadcast transform
    geometry_msgs::msg::TransformStamped transform_stamped;
    transform_stamped.header.stamp = this->now();
    transform_stamped.header.frame_id = cloud_msg->header.frame_id;
    transform_stamped.child_frame_id = frame_id;
    transform_stamped.transform.translation.x = coefficients_sphere->values[0];
    transform_stamped.transform.translation.y = coefficients_sphere->values[1];
    transform_stamped.transform.translation.z = coefficients_sphere->values[2];
    tf2::Quaternion q;
    q.setRPY(0, 0, 0);
    transform_stamped.transform.rotation.x = q.x();
    transform_stamped.transform.rotation.y = q.y();
    transform_stamped.transform.rotation.z = q.z();
    transform_stamped.transform.rotation.w = q.w();
    tf_broadcaster_.sendTransform(transform_stamped);

    // Write the sphere inliers to disk
    extract.setInputCloud(cloud_filtered2);
    extract.setIndices(inliers_sphere);
    extract.setNegative(false);
    PointCloud::Ptr cloud_sphere(new PointCloud());
    extract.filter(*cloud_sphere);

    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(*cloud_sphere, output);
    pub->publish(output);
    pointcloud_to_depth_image(cloud_sphere, image_pub);
  }

  void pointcloud_to_depth_image(const PointCloud::ConstPtr& msg, 
                                rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub)
  {
    float centre_x = 320.5;
    float centre_y = 240.5;
    float focal_x = 554.254691191187;
    float focal_y = 554.254691191187;
    int height = 480;
    int width = 640;

    cv::Mat cv_image = cv::Mat(height, width, CV_32FC1, cv::Scalar(std::numeric_limits<float>::max()));

    for (size_t i = 0; i < msg->points.size(); i++) {
      if (msg->points[i].z == msg->points[i].z) {
        float z = msg->points[i].z * 1000.0;
        float u = (msg->points[i].x * 1000.0 * focal_x) / z;
        float v = (msg->points[i].y * 1000.0 * focal_y) / z;
        int pixel_pos_x = (int)(u + centre_x);
        int pixel_pos_y = (int)(v + centre_y);

        if (pixel_pos_x > (width - 1)) {
          pixel_pos_x = width - 1;
        }
        if (pixel_pos_y > (height - 1)) {
          pixel_pos_y = height - 1;
        }
        cv_image.at<float>(pixel_pos_y, pixel_pos_x) = z;
      }
    }

    cv_image.convertTo(cv_image, CV_8UC1);

    std_msgs::msg::Header header;
    header.frame_id = "camera_depth_optical_frame";
    header.stamp = this->now();
    
    sensor_msgs::msg::Image::SharedPtr output_image = cv_bridge::CvImage(header, "16UC1", cv_image).toImageMsg();
    pub->publish(*output_image);
  }

  void pointcloud_to_rgb_image(const PointCloudRGB::ConstPtr& msg, 
                              rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub)
  {
    float centre_x = 320.5;
    float centre_y = 240.5;
    float focal_x = 554.254691191187;
    float focal_y = 554.254691191187;
    int height = 480;
    int width = 640;

    cv::Mat cv_image = cv::Mat(height, width, CV_8UC3);

    for (size_t i = 0; i < msg->points.size(); i++) {
      if (msg->points[i].z == msg->points[i].z) {
        float z = msg->points[i].z * 1000.0;
        float u = (msg->points[i].x * 1000.0 * focal_x) / z;
        float v = (msg->points[i].y * 1000.0 * focal_y) / z;
        int pixel_pos_x = (int)(u + centre_x);
        int pixel_pos_y = (int)(v + centre_y);

        int r = msg->points[i].r;
        int g = msg->points[i].g;
        int b = msg->points[i].b;

        if (pixel_pos_x > (width - 1)) {
          pixel_pos_x = width - 1;
        }
        if (pixel_pos_y > (height - 1)) {
          pixel_pos_y = height - 1;
        }

        cv_image.at<cv::Vec3b>(pixel_pos_y, pixel_pos_x) = cv::Vec3b(b, g, r);
      }
    }

    std_msgs::msg::Header header;
    header.frame_id = "camera_depth_optical_frame";
    header.stamp = this->now();
    
    sensor_msgs::msg::Image::SharedPtr output_image = cv_bridge::CvImage(header, "8UC3", cv_image).toImageMsg();
    pub->publish(*output_image);
  }

private:
  // Publishers for spheres
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_blue_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_red_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_green_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_yellow_sphere_;
  
  // Publishers for cylinders
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_red_cylinder_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_green_cylinder_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_blue_cylinder_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_yellow_cylinder_;

  // Publishers for filtered clouds
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_blue_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_red_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_green_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_yellow_;

  // Publishers for filtered images
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_blue_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_red_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_green_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_yellow_;

  // Publishers for object images
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_blue_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_red_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_green_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_yellow_sphere_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_red_cylinder_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_green_cylinder_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_blue_cylinder_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_yellow_cylinder_;

  // Subscribers for sphere detection
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_red_sphere_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_green_sphere_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_blue_sphere_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_yellow_sphere_;
  
  // Subscribers for cylinder detection
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_red_cylinder_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_green_cylinder_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_blue_cylinder_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_yellow_cylinder_;

  // Subscribers for color filtering
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_blue_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_red_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_green_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_yellow_;

  // Transform broadcaster
  tf2_ros::TransformBroadcaster tf_broadcaster_;
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ObjectDetection>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
