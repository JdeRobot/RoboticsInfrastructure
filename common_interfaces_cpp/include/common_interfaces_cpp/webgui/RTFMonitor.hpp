#ifndef RTF_MONITOR_HPP_
#define RTF_MONITOR_HPP_

#include <atomic>
#include <thread>
#include <string>
#include <chrono>

class RTFMonitor {
public:
    explicit RTFMonitor(const std::string& stats_topic = "/stats",
                        std::chrono::milliseconds interval = std::chrono::milliseconds(500));
    ~RTFMonitor();

    double get() const;

private:
    void loop();
    double poll();

    std::string topic_;
    std::chrono::milliseconds interval_;
    std::atomic<double> value_;
    std::atomic<bool> running_;
    std::thread thread_;
};

#endif