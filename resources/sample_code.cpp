#include <iostream>
#include <vector>
#include <numeric>

// A simple utility function that is a prime candidate for inlining.
int utility_function(int a) {
    if (a < 0) {
        return 0;
    }
    return (a * 2) + 1;
}

// A function with more complex logic (loops, conditions).
int complex_logic_function(int x, int y) {
    int total = 0;
    if (x > y) {
        for (int i = 0; i < x; ++i) {
            total += utility_function(i) - i;
        }
    } else {
        total = utility_function(y) + x;
    }
    return total;
}

// A function whose primary characteristic is calling other functions.
void caller_function() {
    std::cout << "Calling utility..." << std::endl;
    int res1 = utility_function(10);
    int res2 = utility_function(20);
    int res3 = utility_function(res1 + res2);
    std::cout << "Result: " << res3 << std::endl;
}

// A larger function with a more substantial body.
double large_body_function(const std::vector<double>& data) {
    double sum = 0.0;
    double sum_sq = 0.0;

    if (data.empty()) {
        return 0.0; // Early exit
    }

    for (double val : data) {
        sum += val;
        sum_sq += val * val;
        // This print statement adds to the function's body size
        std::cout << "Processing value: " << val << std::endl;
    }

    double mean = sum / data.size();
    double variance = (sum_sq / data.size()) - (mean * mean);

    if (variance < 0) {
        variance = 0;
    }

    return variance;
}


int main() {
    std::cout << "Starting application..." << std::endl;
    complex_logic_function(5, 10);
    caller_function();
    std::vector<double> my_data = {1.1, 2.2, 3.3, 4.4, 5.5};
    large_body_function(my_data);
    std::cout << "Application finished." << std::endl;
    return 0;
}