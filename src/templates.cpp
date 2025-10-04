#include <iostream>
#include <string>

// A templated function that performs several operations.
// The compiler will create a separate version of this function for every
// type it is called with (int, double, float, etc.).
template<typename T>
void process_value(T value) {
    T result = (value * 2) / 1.5;
    std::cout << "Original: " << value
              << ", Processed: " << result
              << std::endl;
    if (result > 100) {
        std::cout << "Result is large!" << std::endl;
    }
}

// A simple non-templated function for comparison.
void standalone_function() {
    std::cout << "This is a standalone function." << std::endl;
}

// Main instantiates the template with four different types, forcing
// the compiler to generate four distinct versions of process_value.
int main() {
    process_value<int>(10);
    process_value<double>(20.5);
    process_value<float>(30.5f);
    process_value<short>(5);

    standalone_function();
    return 0;
}