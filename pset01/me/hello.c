#include <cs50.h>
#include <stdio.h>

int main(void)
{
    // Input a name
    string name = get_string("What's your name? ");

    // Say "hello" to that name
    printf("hello, %s. Im happy and proud for u. Keep going\n", name);
}
