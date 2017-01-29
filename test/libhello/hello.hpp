#pragma once

#ifdef _MSC_VER
#   ifdef HELLO_EXPORT
#       define HELLO_API __declspec(dllexport)
#   else
#       define HELLO_API
#   endif
#else
#   define HELLO_API
#endif

extern "C" {
int HELLO_API hello();
}
