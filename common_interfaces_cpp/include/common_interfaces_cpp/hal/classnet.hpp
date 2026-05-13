#ifndef COMMON_INTERFACES_CPP__CLASSNET_HPP_
#define COMMON_INTERFACES_CPP__CLASSNET_HPP_

#include <string>
#include <vector>
#include <map>
#include <mutex>
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>

extern const std::string FROZEN_GRAPH;
extern const std::string PB_TXT;
extern const int SIZE;

extern const std::map<int, std::string> LABEL_MAP;

class BoundingBox {
public:
    BoundingBox(
        int identifier,
        const std::string& class_id_str,
        float score,
        float xmin,
        float ymin,
        float xmax,
        float ymax
    );

    int id;
    std::string class_id;
    float score;
    float xmin;
    float ymin;
    float xmax;
    float ymax;

    std::string to_string() const;
};

class NeuralNetwork {
public:
    NeuralNetwork();

    cv::Mat detect(const cv::Mat& img);
    std::vector<BoundingBox> getBoundingBoxes(const cv::Mat& img);

private:
    cv::dnn::Net net;
    std::mutex net_mutex_;
};

#endif