#ifndef WEBUI_BRIDGE_HPP_
#define WEBUI_BRIDGE_HPP_

#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/strand.hpp>
#include <boost/asio/executor_work_guard.hpp>
#include <nlohmann/json.hpp>
#include <rclcpp/rclcpp.hpp>
#include <opencv2/opencv.hpp>
#include <string>
#include <thread>
#include <mutex>
#include <memory>
#include <functional>
#include <vector>
#include <chrono>
#include <atomic>
#include <optional>

namespace beast     = boost::beast;
namespace websocket = beast::websocket;
namespace net       = boost::asio;
using tcp           = net::ip::tcp;
using json          = nlohmann::json;

// WebSocketSession
// Manages a single async WebSocket client connection.
// Thread-safe send queue: call send() from any thread.

class WebSocketSession : public std::enable_shared_from_this<WebSocketSession>
{
public:
    explicit WebSocketSession(net::io_context& ioc);

    void run(const std::string& host, const std::string& port);
    void send(const std::string& msg);
    void set_on_message(std::function<void(const std::string&)> cb);

private:
    void on_resolve  (beast::error_code ec, tcp::resolver::results_type results);
    void on_connect  (beast::error_code ec, tcp::resolver::results_type::endpoint_type ep);
    void on_handshake(beast::error_code ec);
    void on_read     (beast::error_code ec, std::size_t);
    void on_write    (beast::error_code ec, std::size_t);
    void do_write    ();

    tcp::resolver                           resolver_;
    websocket::stream<beast::tcp_stream>    ws_;
    beast::flat_buffer                      buffer_;
    std::string                             host_;
    std::vector<std::string>                send_queue_;
    std::mutex                              queue_mtx_;
    bool                                    writing_{ false };
    std::function<void(const std::string&)> on_message_;
};

// ---------------------------------------------------------------------------
// BaseWebGUI
//
// Derive from this class to implement an exercise GUI.
// Override:
//   json update_gui()               — called at gui_freq Hz, return JSON to send
//   void on_frontend_message(msg)   — called when the frontend sends something
//
// Call send_to_frontend(json) from anywhere to push an unsolicited message.
// ---------------------------------------------------------------------------
class BaseWebGUI : public rclcpp::Node
{
public:
    // node_name : ROS node name
    // host/port : WebSocket server address (the frontend's WS server)
    // gui_freq  : Hz at which update_gui() is called
    BaseWebGUI(const std::string& node_name,
               const std::string& host,
               const std::string& port,
               double             gui_freq);

    virtual ~BaseWebGUI();

    // --- Override these ---
    virtual json update_gui() = 0;
    virtual void on_frontend_message(const std::string& msg) {}

    // Send an arbitrary JSON payload to the frontend immediately
    void send_to_frontend(const json& payload);

    // Base64 utility (available to subclasses)
    static std::string base64_encode(const unsigned char* data, size_t len);

protected:
    double gui_freq_;

private:
    void on_ws_message(const std::string& msg);
    void gui_timer_cb();

    // WebSocket (runs on its own io_context thread)
    net::io_context                                                    ioc_;
    std::optional<net::executor_work_guard<net::io_context::executor_type>> work_guard_;
    std::shared_ptr<WebSocketSession>                                  ws_session_;
    std::thread                                                        ioc_thread_;

    // ROS timer
    rclcpp::TimerBase::SharedPtr gui_timer_;
};

#endif // WEBUI_BRIDGE_HPP_