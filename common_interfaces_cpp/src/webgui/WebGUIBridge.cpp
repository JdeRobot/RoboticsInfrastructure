#include "common_interfaces_cpp/webgui/WebGUIBridge.hpp"

WebSocketSession::WebSocketSession(net::io_context& ioc)
    : resolver_(net::make_strand(ioc)), ws_(net::make_strand(ioc)), is_writing_(false) {}

void WebSocketSession::run(const std::string& host, const std::string& port)
{
    host_ = host;
    buffer_.max_size(1024 * 1024 * 10);
    resolver_.async_resolve(host, port, beast::bind_front_handler(&WebSocketSession::on_resolve, shared_from_this()));
}

void WebSocketSession::set_message_callback(std::function<void(const std::string&)> cb)
{
    message_callback_ = cb;
}

void WebSocketSession::send(const std::string& msg)
{
    std::lock_guard<std::mutex> lock(queue_mutex_);
    write_queue_.push_back(msg);
    if (!is_writing_) {
        is_writing_ = true;
        ws_.async_write(net::buffer(write_queue_.front()), beast::bind_front_handler(&WebSocketSession::on_write, shared_from_this()));
    }
}

void WebSocketSession::on_resolve(beast::error_code ec, tcp::resolver::results_type results)
{
    if (ec) return;
    beast::get_lowest_layer(ws_).expires_after(std::chrono::seconds(30));
    beast::get_lowest_layer(ws_).async_connect(results, beast::bind_front_handler(&WebSocketSession::on_connect, shared_from_this()));
}

void WebSocketSession::on_connect(beast::error_code ec, tcp::resolver::results_type::endpoint_type ep)
{
    if (ec) return;
    beast::get_lowest_layer(ws_).expires_never();
    ws_.set_option(websocket::stream_base::timeout::suggested(beast::role_type::client));
    ws_.read_message_max(1024 * 1024 * 10);
    ws_.auto_fragment(false);
    host_ += ':' + std::to_string(ep.port());
    ws_.async_handshake(host_, "/", beast::bind_front_handler(&WebSocketSession::on_handshake, shared_from_this()));
}

void WebSocketSession::on_handshake(beast::error_code ec)
{
    if (ec) return;
    ws_.async_read(buffer_, beast::bind_front_handler(&WebSocketSession::on_read, shared_from_this()));
}

void WebSocketSession::on_write(beast::error_code ec, std::size_t)
{
    std::lock_guard<std::mutex> lock(queue_mutex_);
    write_queue_.erase(write_queue_.begin());
    if (ec) {
        is_writing_ = false;
        return;
    }
    if (!write_queue_.empty()) {
        ws_.async_write(net::buffer(write_queue_.front()), beast::bind_front_handler(&WebSocketSession::on_write, shared_from_this()));
    } else {
        is_writing_ = false;
    }
}

void WebSocketSession::on_read(beast::error_code ec, std::size_t)
{
    if (ec) return;
    std::string msg = beast::buffers_to_string(buffer_.data());
    buffer_.consume(buffer_.size());

    if (message_callback_) {
        message_callback_(msg);
    }

    ws_.async_read(buffer_, beast::bind_front_handler(&WebSocketSession::on_read, shared_from_this()));
}

BaseWebGUI::BaseWebGUI(const std::string& node_name, const std::string& host, const std::string& port, double freq)
    : Node(node_name), real_time_factor_(0.0), ack_frontend_(false), ack_(true), brain_freq_(0.0), gui_freq_(freq)
{
    ws_session_ = std::make_shared<WebSocketSession>(ioc_);
    ws_session_->set_message_callback(std::bind(&BaseWebGUI::process_message, this, std::placeholders::_1));
    ws_session_->run(host, port);

    ioc_thread_ = std::thread([this]() { ioc_.run(); });

    perf_sub_ = this->create_subscription<gazebo_msgs::msg::PerformanceMetrics>(
        "/performance_metrics", 10, std::bind(&BaseWebGUI::performance_callback, this, std::placeholders::_1));

    auto period = std::chrono::duration<double>(1.0 / freq);
    gui_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::nanoseconds>(period),
        std::bind(&BaseWebGUI::gui_timer_callback, this));
}

BaseWebGUI::~BaseWebGUI()
{
    ioc_.stop();
    if (ioc_thread_.joinable()) {
        ioc_thread_.join();
    }
}

void BaseWebGUI::process_message(const std::string& msg)
{
    if (msg.find("ack") != std::string::npos) {
        std::lock_guard<std::mutex> lock(ack_lock_);
        ack_ = true;
    } else if (msg.find("start") != std::string::npos) {
        std::lock_guard<std::mutex> lock(ack_lock_);
        ack_frontend_ = true;
    }
}

std::vector<rclcpp::Node::SharedPtr> BaseWebGUI::get_nodes()
{
    return {shared_from_this()};
}

void BaseWebGUI::send_to_client(const std::string& msg)
{
    if (ws_session_) {
        ws_session_->send(msg);
    }
}

void BaseWebGUI::performance_callback(const gazebo_msgs::msg::PerformanceMetrics::SharedPtr msg)
{
    real_time_factor_ = msg->real_time_factor;
}

void BaseWebGUI::gui_timer_callback()
{
    std::lock_guard<std::mutex> lock(ack_lock_);
    if (ack_frontend_ && ack_) {
        json payload = update_gui();
        
        payload["rtf"] = real_time_factor_;
        payload["brain"] = brain_freq_;
        payload["gui"] = gui_freq_;
        payload["fps"] = -1.0;
        payload["lat"] = -1.0;

        send_to_client(payload.dump());
        ack_ = false;
    }
}