#include "common_interfaces_cpp/webgui/MeasuringThreadingGUI.hpp"
#include <chrono>
#include <regex>
#include <cstdio>
#include <cmath>
#include <vector>

namespace beast = boost::beast;
namespace websocket = beast::websocket;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;

class WSSession : public std::enable_shared_from_this<WSSession> {
    tcp::resolver resolver_;
    websocket::stream<beast::tcp_stream> ws_;
    beast::flat_buffer buffer_;
    MeasuringThreadingGUI* gui_;
    std::string host_;
    std::string port_;
    net::steady_timer timer_;
    std::vector<std::string> write_queue_;
    double out_period_;

public:
    explicit WSSession(net::io_context& ioc, MeasuringThreadingGUI* gui, const std::string& host, const std::string& port, double out_period)
        : resolver_(net::make_strand(ioc)), ws_(net::make_strand(ioc)), gui_(gui), host_(host), port_(port), timer_(net::make_strand(ioc)), out_period_(out_period) {}

    void run() {
        resolver_.async_resolve(host_, port_, beast::bind_front_handler(&WSSession::on_resolve, shared_from_this()));
    }

    void on_resolve(beast::error_code ec, tcp::resolver::results_type results) {
        if (ec) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            run();
            return;
        }
        beast::get_lowest_layer(ws_).expires_after(std::chrono::seconds(30));
        beast::get_lowest_layer(ws_).async_connect(results, beast::bind_front_handler(&WSSession::on_connect, shared_from_this()));
    }

    void on_connect(beast::error_code ec, tcp::resolver::results_type::endpoint_type ep) {
        if (ec) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            run();
            return;
        }
        beast::get_lowest_layer(ws_).expires_never();
        ws_.set_option(websocket::stream_base::timeout::suggested(beast::role_type::client));
        ws_.read_message_max(1024 * 1024 * 10);
        ws_.auto_fragment(false);
        std::string h = host_ + ":" + std::to_string(ep.port());
        ws_.async_handshake(h, "/", beast::bind_front_handler(&WSSession::on_handshake, shared_from_this()));
    }

    void on_handshake(beast::error_code ec) {
        if (ec) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            run();
            return;
        }
        gui_->set_session(shared_from_this());
        do_read();

        timer_.expires_after(std::chrono::milliseconds(static_cast<int>(out_period_ * 1000)));
        timer_.async_wait(beast::bind_front_handler(&WSSession::on_timer, shared_from_this()));
    }

    void do_read() {
        ws_.async_read(buffer_, beast::bind_front_handler(&WSSession::on_read, shared_from_this()));
    }

    void on_read(beast::error_code ec, std::size_t) {
        if (ec) {
            gui_->set_session(nullptr);
            std::this_thread::sleep_for(std::chrono::seconds(1));
            run();
            return;
        }
        std::string msg = beast::buffers_to_string(buffer_.data());
        buffer_.consume(buffer_.size());
        gui_->gui_in_thread(msg);
        do_read();
    }

    void on_timer(beast::error_code ec) {
        if (ec) return;

        gui_->trigger_update();

        timer_.expires_after(std::chrono::milliseconds(static_cast<int>(out_period_ * 1000)));
        timer_.async_wait(beast::bind_front_handler(&WSSession::on_timer, shared_from_this()));
    }

    void send(const std::string& msg) {
        net::post(ws_.get_executor(), beast::bind_front_handler(&WSSession::do_send, shared_from_this(), msg));
    }

    void do_send(const std::string& msg) {
        bool writing = !write_queue_.empty();
        write_queue_.push_back(msg);
        if (!writing) {
            ws_.async_write(net::buffer(write_queue_.front()), beast::bind_front_handler(&WSSession::on_write, shared_from_this()));
        }
    }

    void on_write(beast::error_code ec, std::size_t) {
        if (ec) {
            gui_->set_session(nullptr);
            std::this_thread::sleep_for(std::chrono::seconds(1));
            run();
            return;
        }
        write_queue_.erase(write_queue_.begin());
        if (!write_queue_.empty()) {
            ws_.async_write(net::buffer(write_queue_.front()), beast::bind_front_handler(&WSSession::on_write, shared_from_this()));
        }
    }

    void close() {
        if (ws_.is_open()) {
            beast::error_code ec;
            ws_.close(websocket::close_code::normal, ec);
        }
    }
};

MeasuringThreadingGUI::MeasuringThreadingGUI(const std::string& host, const std::string& port, double freq, const std::string& world_name)
    : host_(host), port_(port), world_name_(world_name), out_period_(1.0 / freq),
      ack_(true), ack_frontend_(false), ideal_cycle_(80.0), real_time_factor_(0.0),
      iteration_counter_(0), fps_(-1), lat_(-1), running_(true), session_(nullptr) {}

MeasuringThreadingGUI::~MeasuringThreadingGUI() {
    running_ = false;
    
    if (session_) {
        std::static_pointer_cast<WSSession>(session_)->close();
    }
    ioc_.stop();

    if (ioc_thread_.joinable()) ioc_thread_.join();
    if (rtf_thread_.joinable()) rtf_thread_.join();
    if (freq_thread_.joinable()) freq_thread_.join();
}

void MeasuringThreadingGUI::start() {
    rtf_thread_ = std::thread(&MeasuringThreadingGUI::get_real_time_factor, this);
    freq_thread_ = std::thread(&MeasuringThreadingGUI::measure_and_send_frequency, this);

    auto session = std::make_shared<WSSession>(ioc_, this, host_, port_, out_period_);
    session->run();
    ioc_thread_ = std::thread([this]() { ioc_.run(); });
}

void MeasuringThreadingGUI::set_session(std::shared_ptr<void> session) {
    std::lock_guard<std::mutex> lock(session_mutex_);
    session_ = session;
}

void MeasuringThreadingGUI::gui_in_thread(const std::string& message) {
    std::lock_guard<std::mutex> lock(ack_lock_);
    if (message.find("ack") != std::string::npos) {
        ack_ = true;
    } else if (message.find("start") != std::string::npos) {
        ack_frontend_ = true;
    }
}

void MeasuringThreadingGUI::trigger_update() {
    iteration_counter_++;
    bool should_update = false;
    {
        std::lock_guard<std::mutex> lock(ack_lock_);
        if (ack_frontend_ && ack_) {
            should_update = true;
            ack_ = false;
        }
    }

    if (should_update) {
        update_gui();
    }
}

void MeasuringThreadingGUI::send_to_client(const std::string& msg) {
    std::lock_guard<std::mutex> lock(session_mutex_);
    if (session_) {
        std::static_pointer_cast<WSSession>(session_)->send(msg);
    }
}

void MeasuringThreadingGUI::get_real_time_factor() {
    while (running_) {
        std::this_thread::sleep_for(std::chrono::seconds(2));
        std::string cmd = "gz topic -e -t /world/" + world_name_ + "/stats --num 1 2>/dev/null";
        FILE* pipe = popen(cmd.c_str(), "r");
        if (!pipe) continue;

        char buffer[128];
        std::string result;
        while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
            result += buffer;
        }
        pclose(pipe);

        std::regex r("real_time_factor:\\s*([0-9\\.]+)");
        std::smatch match;
        if (std::regex_search(result, match, r)) {
            double rtf = std::stod(match[1].str());
            real_time_factor_ = std::round(rtf * 1000.0) / 1000.0;
        }
    }
}

void MeasuringThreadingGUI::measure_and_send_frequency() {
    auto previous_time = std::chrono::steady_clock::now();
    
    while (running_) {
        std::this_thread::sleep_for(std::chrono::seconds(2));
        auto current_time = std::chrono::steady_clock::now();
        std::chrono::duration<double, std::milli> dt = current_time - previous_time;
        previous_time = current_time;

        int iters = iteration_counter_.exchange(0);
        double measured_cycle = (iters > 0) ? (dt.count() / iters) : 0.0;
        double brain_frequency = (measured_cycle != 0.0) ? (1000.0 / measured_cycle) : 0.0;
        brain_frequency = std::round(brain_frequency * 10.0) / 10.0;
        
        double gui_frequency = std::round((1000.0 / ideal_cycle_) * 10.0) / 10.0;

        nlohmann::json freq_msg = {
            {"brain", brain_frequency},
            {"gui", gui_frequency},
            {"rtf", real_time_factor_.load()},
            {"fps", fps_.load()},
            {"lat", lat_.load()}
        };

        send_to_client(freq_msg.dump());
    }
}