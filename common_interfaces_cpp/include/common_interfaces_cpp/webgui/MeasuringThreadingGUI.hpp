#ifndef MEASURING_THREADING_GUI_HPP_
#define MEASURING_THREADING_GUI_HPP_

#include <string>
#include <thread>
#include <mutex>
#include <atomic>
#include <memory>
#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/strand.hpp>
#include <boost/asio/steady_timer.hpp>
#include <nlohmann/json.hpp>

class MeasuringThreadingGUI {
public:
    MeasuringThreadingGUI(const std::string& host = "127.0.0.1", const std::string& port = "2303", double freq = 30.0, const std::string& world_name = "default");
    virtual ~MeasuringThreadingGUI();

    void start();
    void send_to_client(const std::string& msg);

    void gui_in_thread(const std::string& message);
    void trigger_update();
    void set_session(std::shared_ptr<void> session);

protected:
    virtual void update_gui() = 0;

    std::string host_;
    std::string port_;
    std::string world_name_;
    double out_period_;

    bool ack_;
    bool ack_frontend_;
    std::mutex ack_lock_;

    double ideal_cycle_;
    std::atomic<double> real_time_factor_;
    std::atomic<int> iteration_counter_;
    std::atomic<int> fps_;
    std::atomic<int> lat_;

    std::atomic<bool> running_;

private:
    void get_real_time_factor();
    void measure_and_send_frequency();

    boost::asio::io_context ioc_;
    std::thread ioc_thread_;
    std::thread rtf_thread_;
    std::thread freq_thread_;

    std::shared_ptr<void> session_;
    std::mutex session_mutex_;
};

#endif