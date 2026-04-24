#include "common_interfaces_cpp/webgui/RTFMonitor.hpp"
#include <cstdio>
#include <algorithm>
#include <cmath>

RTFMonitor::RTFMonitor(const std::string& stats_topic, std::chrono::milliseconds interval)
    : topic_(stats_topic), interval_(interval), value_(0.0), running_(true) {
    thread_ = std::thread(&RTFMonitor::loop, this);
}

RTFMonitor::~RTFMonitor() {
    running_.store(false);
    if (thread_.joinable()) {
        thread_.join();
    }
}

double RTFMonitor::get() const {
    return value_.load();
}

void RTFMonitor::loop() {
    while (running_.load()) {
        value_.store(poll());
        std::this_thread::sleep_for(interval_);
    }
}

double RTFMonitor::poll() {
    std::string cmd = "gz topic -e -t " + topic_ + " -n 1 2>/dev/null";
    FILE* pipe = popen(cmd.c_str(), "r");
    
    if (!pipe) {
        return value_.load();
    }

    double result = value_.load();
    char buf[256];
    
    while (fgets(buf, sizeof(buf), pipe)) {
        std::string line(buf);
        auto pos = line.find("real_time_factor:");
        
        if (pos != std::string::npos) {
            try {
                std::string val = line.substr(pos + 17);
                val.erase(std::remove_if(val.begin(), val.end(),
                    [](char c){ return c == ' ' || c == '\n' || c == '\r'; }), val.end());
                
                double raw = std::stod(val);
                result = std::round(raw * 100.0) / 100.0;
            } catch (...) {}
            break;
        }
    }
    
    pclose(pipe);
    return result;
}