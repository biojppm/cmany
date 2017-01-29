
#include "hello.hpp"
#include <iostream>

int HELLO_API hello()
{
    auto s = (8 * sizeof(void*));
    std::cout << s << std::endl;
    return (int)s;
}
