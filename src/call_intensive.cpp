#include <vector>

// This is a very small function. The cost of calling it is high
// relative to the work it does. Inlining it should have a major impact
// when it's called thousands of times.
int simple_increment(int a) {
    return a + 1;
}

// This function calls the helper in a deeply nested loop,
// creating thousands of call sites.
int process_data_grid() {
    int total = 0;
    for (int i = 0; i < 200; ++i) {
        for (int j = 0; j < 200; ++j) {
            // This call will be repeated 40,000 times.
            total += simple_increment(i * j);
        }
    }
    return total;
}

int main() {
    process_data_grid();
    return 0;
}
