
#ifndef _STRING_PRINTF_HPP
#define _STRING_PRINTF_HPP

#include <cstdarg> // for va_list, va_start
#include <string>

namespace ros2_shared
{
  struct string_print {
    static std::string f(std::string fmt_str, ...)
    {
      va_list ap;
      constexpr size_t string_reserve = 32;
      std::string::size_type str_len = std::max(fmt_str.size(), string_reserve);

      // Constructs the string with count copies of character ch.
      // In C++11 and later, mystring.c_str() is equivalent to mystring.data() is equivalent to
      // &mystring[0], and mystring[mystring.size()] is guaranteed to be '\0'
      std::string str(str_len, '\0'); // Don't use braces! Allocates str_len nulls and then one for the terminator.

      // Writes the results to a character string buffer. At most buf_size-1 characters are written.
      // The resulting character string will be terminated with a null character, unless buf_size is zero.
      //
      // final_n is the number of characters written if successful or negative value if an error occurred.
      // If the resulting string gets truncated due to buf_size limit, function returns the total number of characters
      // (not including the terminating null-byte) which would have been written, if the limit was not imposed.
      va_start(ap, fmt_str);
      auto final_n = std::vsnprintf(&str.front(), str_len + 1, fmt_str.c_str(), ap);
      va_end(ap);

      // For an encoding error return an empty string.
      if (final_n < 0) {
        return std::string{};
      }

      // If the characters written fit in the std::string, then resize the string and return it.
      auto new_str_len = static_cast<std::string::size_type>(final_n);
      if (new_str_len <= str_len) {
        if (new_str_len < str_len) {
          str.resize(new_str_len);
        }
        return str;
      }

      // Resize the string and do the conversion again
      str_len = new_str_len;
      str.resize(str_len, '\0');
      va_start(ap, fmt_str);
      final_n = std::vsnprintf(&str.front(), str_len + 1, fmt_str.c_str(), ap);
      va_end(ap);

      // Resize a valid string if needed and return it
      if (final_n > 0) {
        new_str_len = static_cast<std::string::size_type>(final_n);
        if (new_str_len <= str_len) {
          if (new_str_len < str_len) {
            str.resize(new_str_len);
          }
          return str;
        }
      }

      return std::string{};
    }

  };

#if 0
  std::string string_printf(std::string fmt_str, ...)
  {
    constexpr size_t string_reserve = 32;
    size_t str_len = std::max(fmt_str.size(), string_reserve);
    std::string str;

    do {
      va_list ap;
      va_start(ap, fmt_str); // NOTE: vsnprintf modifies ap so it has to be initialized in the loop

      str.resize(str_len);

      auto final_n = vsnprintf(const_cast<char *>(str.data()), str_len, fmt_str.c_str(), ap);

      // For an encoding error just return what is in the buffer.
      if (final_n < 0) {
        break;
      }

      auto final_n_ = static_cast<size_t>(final_n);
      // If the buffer sufficient, resize it and finish.
      if (final_n_ < str_len) {
        str.resize(final_n_ + 1); // don't truncate the trailing null!
        break;
      }

      // The buffer was not large enough. So resize it.
      str_len = final_n_ + 1;

      va_end(ap);
    } while (true);

    return str;
  }
#endif
}
#endif //_STRING_PRINTF_HPP
