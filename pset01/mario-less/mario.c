#include <cs50.h>
#include <stdio.h>

void make_piramide(int h);

int main(void)
{
    // Promt to de user for a Height > 0
    int n;
    do
    {
        n = get_int("height: ");
    }
    while (n < 1 || n > 8);

    // Make a piramide with Height n
    make_piramide(n);
}

void make_piramide(int h)
{
    int x = h - 1;

    for (int i = 0; i < h; i++)
    {
        for (int j = 0; j < x; j++)
        {
            printf(" ");
        }
        for (int j = 0; j < h - x; j++)
        {
            printf("#");
        }
        x--;
        printf("\n");
    }
}
