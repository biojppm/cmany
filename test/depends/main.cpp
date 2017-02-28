#include "hello.hpp"
#include <gtest/gtest.h>

TEST(libhello, just_do_it)
{
    EXPECT_EQ(hello(), sizeof(void*)*8);
}

int main(int argc, char* argv[])
{
    int stat = RUN_ALL_TESTS();
    return stat;
}
