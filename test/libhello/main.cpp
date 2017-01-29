#include "hello.hpp"
#include <iostream>

int main(int argc, char* argv[])
{
    int s = hello();
    std::cout << "yep, it's " << s << " indeed" << std::endl;
    return 0;
}
