#include "common_interfaces_cpp/webgui/WebGUIBridge.hpp"

// ---------------------------------------------------------------------------
// WebSocketSession
// ---------------------------------------------------------------------------

WebSocketSession::WebSocketSession(net::io_context& ioc)
    : resolver_(net::make_strand(ioc))
    , ws_(net::make_strand(ioc))
{}

void WebSocketSession::set_on_message(std::function<void(const std::string&)> cb)
{
    on_message_ = std::move(cb);
}

void WebSocketSession::run(const std::string& host, const std::string& port)
{
    host_ = host;
    buffer_.max_size(10 * 1024 * 1024);
    resolver_.async_resolve(host, port,
        beast::bind_front_handler(&WebSocketSession::on_resolve, shared_from_this()));
}

void WebSocketSession::on_resolve(beast::error_code ec, tcp::resolver::results_type results)
{
    if (ec) { RCLCPP_ERROR(rclcpp::get_logger("WebGUI"), "resolve: %s", ec.message().c_str()); return; }
    beast::get_lowest_layer(ws_).expires_after(std::chrono::seconds(30));
    beast::get_lowest_layer(ws_).async_connect(results,
        beast::bind_front_handler(&WebSocketSession::on_connect, shared_from_this()));
}

void WebSocketSession::on_connect(beast::error_code ec, tcp::resolver::results_type::endpoint_type ep)
{
    if (ec) { RCLCPP_ERROR(rclcpp::get_logger("WebGUI"), "connect: %s", ec.message().c_str()); return; }
    beast::get_lowest_layer(ws_).expires_never();
    ws_.set_option(websocket::stream_base::timeout::suggested(beast::role_type::client));
    ws_.read_message_max(10 * 1024 * 1024);
    ws_.auto_fragment(false);
    host_ += ':' + std::to_string(ep.port());
    ws_.async_handshake(host_, "/",
        beast::bind_front_handler(&WebSocketSession::on_handshake, shared_from_this()));
}

void WebSocketSession::on_handshake(beast::error_code ec)
{
    if (ec) { RCLCPP_ERROR(rclcpp::get_logger("WebGUI"), "handshake: %s", ec.message().c_str()); return; }
    RCLCPP_INFO(rclcpp::get_logger("WebGUI"), "WebSocket connected");
    ws_.async_read(buffer_,
        beast::bind_front_handler(&WebSocketSession::on_read, shared_from_this()));
}

void WebSocketSession::on_read(beast::error_code ec, std::size_t)
{
    if (ec) { RCLCPP_WARN(rclcpp::get_logger("WebGUI"), "read: %s", ec.message().c_str()); return; }

    std::string msg = beast::buffers_to_string(buffer_.data());
    buffer_.consume(buffer_.size());

    if (on_message_) on_message_(msg);

    ws_.async_read(buffer_,
        beast::bind_front_handler(&WebSocketSession::on_read, shared_from_this()));
}

void WebSocketSession::send(const std::string& msg)
{
    std::lock_guard<std::mutex> lk(queue_mtx_);
    send_queue_.push_back(msg);
    if (!writing_) do_write();
}

void WebSocketSession::do_write()
{
    if (send_queue_.empty()) { writing_ = false; return; }
    writing_ = true;
    ws_.async_write(net::buffer(send_queue_.front()),
        beast::bind_front_handler(&WebSocketSession::on_write, shared_from_this()));
}

void WebSocketSession::on_write(beast::error_code ec, std::size_t)
{
    std::lock_guard<std::mutex> lk(queue_mtx_);
    send_queue_.erase(send_queue_.begin());
    if (ec) { writing_ = false; RCLCPP_WARN(rclcpp::get_logger("WebGUI"), "write: %s", ec.message().c_str()); return; }
    do_write();
}

// ---------------------------------------------------------------------------
// BaseWebGUI
// ---------------------------------------------------------------------------

BaseWebGUI::BaseWebGUI(const std::string& node_name,
                       const std::string& host,
                       const std::string& port,
                       double             gui_freq)
    : rclcpp::Node(node_name)
    , gui_freq_(gui_freq)
{
    // Keep ioc_ alive even before the WS connects
    work_guard_.emplace(net::make_work_guard(ioc_));

    ws_session_ = std::make_shared<WebSocketSession>(ioc_);
    ws_session_->set_on_message([this](const std::string& msg) {
        on_ws_message(msg);
    });
    ws_session_->run(host, port);

    ioc_thread_ = std::thread([this]() { ioc_.run(); });

    // ROS timer — fires at gui_freq Hz, always sends
    auto period = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::duration<double>(1.0 / gui_freq));
    gui_timer_ = this->create_wall_timer(period,
        std::bind(&BaseWebGUI::gui_timer_cb, this));
}

BaseWebGUI::~BaseWebGUI()
{
    work_guard_.reset();
    ioc_.stop();
    if (ioc_thread_.joinable()) ioc_thread_.join();
}

void BaseWebGUI::on_ws_message(const std::string& msg)
{
    on_frontend_message(msg);
}

void BaseWebGUI::gui_timer_cb()
{
    json payload = update_gui();
    send_to_frontend(payload);
}

void BaseWebGUI::send_to_frontend(const json& payload)
{
    if (ws_session_) ws_session_->send(payload.dump());
}

std::string BaseWebGUI::base64_encode(const unsigned char* data, size_t len)
{
    static const char lut[] =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    out.reserve((len + 2) / 3 * 4);
    unsigned char a3[3], a4[4];
    int i = 0, j = 0;
    while (len--) {
        a3[i++] = *(data++);
        if (i == 3) {
            a4[0] = (a3[0] & 0xfc) >> 2;
            a4[1] = ((a3[0] & 0x03) << 4) | ((a3[1] & 0xf0) >> 4);
            a4[2] = ((a3[1] & 0x0f) << 2) | ((a3[2] & 0xc0) >> 6);
            a4[3] =   a3[2] & 0x3f;
            for (i = 0; i < 4; i++) out += lut[a4[i]];
            i = 0;
        }
    }
    if (i) {
        for (j = i; j < 3; j++) a3[j] = 0;
        a4[0] = (a3[0] & 0xfc) >> 2;
        a4[1] = ((a3[0] & 0x03) << 4) | ((a3[1] & 0xf0) >> 4);
        a4[2] = ((a3[1] & 0x0f) << 2) | ((a3[2] & 0xc0) >> 6);
        for (j = 0; j < i + 1; j++) out += lut[a4[j]];
        while (i++ < 3) out += '=';
    }
    return out;
}