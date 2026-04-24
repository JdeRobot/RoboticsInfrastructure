#ifndef WEBUI_BRIDGE_HPP_
#define WEBUI_BRIDGE_HPP_

#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/strand.hpp>
#include <nlohmann/json.hpp>
#include <rclcpp/rclcpp.hpp>
#include <string>
#include <thread>
#include <mutex>
#include <memory>
#include <functional>
#include <vector>
#include <cstdio>
#include <chrono>
#include <atomic>

namespace beast = boost::beast;
namespace websocket = beast::websocket;
namespace net = boost::asio;
using tcp = net::ip::tcp;
using json = nlohmann::json;

class WebSocketSession : public std::enable_shared_from_this<WebSocketSession>
{
public:
    explicit WebSocketSession(net::io_context& ioc);
    void run(const std::string& host, const std::string& port);
    void send(const std::string& msg);
    void set_message_callback(std::function<void(const std::string&)> cb);

private:
    void on_resolve(beast::error_code ec, tcp::resolver::results_type results);
    void on_connect(beast::error_code ec, tcp::resolver::results_type::endpoint_type ep);
    void on_handshake(beast::error_code ec);
    void on_write(beast::error_code ec, std::size_t bytes_transferred);
    void on_read(beast::error_code ec, std::size_t bytes_transferred);

    tcp::resolver resolver_;
    websocket::stream<beast::tcp_stream> ws_;
    beast::flat_buffer buffer_;
    std::string host_;
    std::vector<std::string> write_queue_;
    std::mutex queue_mutex_;
    bool is_writing_;
    std::function<void(const std::string&)> message_callback_;
};

class BaseWebGUI : public rclcpp::Node
{
public:
    BaseWebGUI(const std::string& node_name, const std::string& host, const std::string& port, double freq, const std::string& stats_topic = "/stats");
    virtual ~BaseWebGUI();

    virtual void process_message(const std::string& msg);
    virtual json update_gui() = 0;
    virtual std::vector<rclcpp::Node::SharedPtr> get_nodes();

    void send_to_client(const std::string& msg);
    static std::string base64_encode(const unsigned char* data, size_t len);

protected:
    double real_time_factor_;
    bool ack_frontend_;
    bool ack_;
    std::mutex ack_lock_;
    double brain_freq_;
    double gui_freq_;
    std::string stats_topic_;

private:
    void gui_timer_callback();
    void stats_timer_callback();

    net::io_context ioc_;
    std::shared_ptr<WebSocketSession> ws_session_;
    std::thread ioc_thread_;

    rclcpp::TimerBase::SharedPtr gui_timer_;
    rclcpp::TimerBase::SharedPtr stats_timer_;

    std::atomic<int> iteration_counter_;
    std::chrono::time_point<std::chrono::steady_clock> last_freq_update_;
};

#endif