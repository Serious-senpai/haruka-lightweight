#include <cassert>
#include <climits>
#include <iostream>
#include <string>
#include <vector>

#define INF INT_MAX

namespace std
{
    template <typename T>
    const T &min(const T &_x, const T &_y, const T &_z)
    {
        return std::min(_x, std::min(_y, _z));
    }
}

int n, m;
std::string original, compare;
std::vector<std::vector<int>> dp;

int distance(int original_index, int compare_index)
{
    if (dp[original_index][compare_index] > -1)
    {
        return dp[original_index][compare_index];
    }

    int result = -1;
    if (original_index == n)
    {
        result = m - compare_index;
    }
    else if (compare_index == m)
    {
        result = n - original_index;
    }
    else if (original[original_index] == compare[compare_index])
    {
        result = distance(original_index + 1, compare_index + 1);
    }
    else
    {
        result = 1 + std::min(distance(original_index, compare_index + 1),
                              distance(original_index + 1, compare_index),
                              distance(original_index + 1, compare_index + 1));
    }

    return dp[original_index][compare_index] = result;
}

int main(int argc, char *argv[])
{
    assert(argc >= 3);
    original = std::string(argv[1]);
    n = original.length();

    int min_diff = INF;
    std::string result;
    for (int i = 2; i < argc; i++)
    {
        compare = std::string(argv[i]);
        m = compare.length();

        dp.clear();
        dp.resize(n + 1, std::vector<int>(m + 1, -1));

        int diff = distance(0, 0);
        if (diff < min_diff)
        {
            min_diff = diff;
            result = compare;
        }
    }

    std::cout << result;
}