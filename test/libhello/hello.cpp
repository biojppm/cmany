
#include "hello.hpp"
#include <iostream>

int HELLO_API hello()
{
    size_t s = (8 * sizeof(void*));
    std::cout << s << std::endl;
    return (int)s;
}
