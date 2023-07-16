#include <fstream>
#include <iostream>

#define BUFFER_SIZE 2048

int main(int argc, char *argv[])
{
    long long total_size = 0;
    std::fstream output = std::fstream(argv[1], std::ios_base::binary | std::ios_base::out | std::ios_base::trunc);
    for (int i = 2; i < argc; i++)
    {
        std::fstream file = std::fstream(argv[i], std::ios_base::binary | std::ios_base::in);

        file.seekg(0, file.end);
        int size = (int)file.tellg(), left = size;
        file.seekg(0, file.beg);

        char buffer[BUFFER_SIZE];
        while (left > 0)
        {
            int buffer_size = std::min(BUFFER_SIZE, left);
            file.read(buffer, buffer_size);
            output.write(buffer, buffer_size);

            left -= buffer_size;
        }

        total_size += size;
    }

    std::cout << total_size;
}