import os
import random
import sys
import shutil
import json

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
GENERATED_SRC_DIR = os.path.join(PROJECT_ROOT, "src_generated")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
TARGET_CONFIG_PATH = os.path.join(DATA_DIR, "target_functions.json")

NUM_FILES_TO_GENERATE = 250


# --- Thematic C++ File Generators ---

def generate_graph_cpp_file(file_index):
    """
    Generates a substantial C++ file focused on graph algorithms, including
    a Dijkstra's shortest path implementation.
    """
    func_names = []
    file_content = """#include <iostream>
#include <vector>
#include <map>
#include <queue>
#include <limits>

// Using a type alias for graph representation for clarity
using AdjacencyList = std::vector<std::vector<std::pair<int, int>>>;

"""
    # Helper function for printing paths
    print_path_name = f"print_path_{file_index}"
    func_names.append(print_path_name)
    file_content += f"""
void {print_path_name}(const std::vector<int>& parent, int j) {{
    if (parent[j] == -1) {{
        std::cout << j;
        return;
    }}
    {print_path_name}(parent, parent[j]);
    std::cout << " -> " << j;
}}
"""
    # Main Dijkstra's algorithm function
    dijkstra_name = f"dijkstra_shortest_path_{file_index}"
    func_names.append(dijkstra_name)
    file_content += f"""
void {dijkstra_name}(const AdjacencyList& adj, int start_node) {{
    int n = adj.size();
    std::vector<int> dist(n, std::numeric_limits<int>::max());
    std::vector<int> parent(n, -1);

    dist[start_node] = 0;
    std::priority_queue<std::pair<int, int>, std::vector<std::pair<int, int>>, std::greater<std::pair<int, int>>> pq;
    pq.push({{0, start_node}});

    while (!pq.empty()) {{
        int u = pq.top().second;
        pq.pop();

        for (const auto& edge : adj[u]) {{
            int v = edge.first;
            int weight = edge.second;
            if (dist[v] > dist[u] + weight) {{
                dist[v] = dist[u] + weight;
                parent[v] = u;
                pq.push({{dist[v], v}});
            }}
        }}
    }}

    std::cout << "Shortest paths from node " << start_node << ":\\n";
    for (int i = 0; i < n; ++i) {{
        std::cout << "  Node " << i << " (dist=" << dist[i] << "): ";
        {print_path_name}(parent, i);
        std::cout << std::endl;
    }}
}}
"""
    # Main function
    file_content += f"""
int main() {{
    int n = {random.randint(6, 9)};
    AdjacencyList adj(n);
    // Create a random graph
    for (int i = 0; i < n; ++i) {{
        int num_edges = random() % (n / 2) + 1;
        for (int j = 0; j < num_edges; ++j) {{
            adj[i].push_back({{rand() % n, rand() % 100 + 1}});
        }}
    }}
    {dijkstra_name}(adj, 0);
    return 0;
}}
"""
    return file_content, func_names


def generate_data_processing_file(file_index):
    """
    Generates a complex data processing pipeline with multiple steps
    like filtering, sorting, and aggregation.
    """
    func_names = []
    file_content = """#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <numeric>

struct DataRecord {
    int id;
    double value;
    int category;
    bool active;
};
"""
    # 1. Filter function
    filter_name = f"filter_active_records_{file_index}"
    func_names.append(filter_name)
    file_content += f"""
std::vector<DataRecord> {filter_name}(const std::vector<DataRecord>& records) {{
    std::vector<DataRecord> filtered;
    for (const auto& rec : records) {{
        if (rec.active && rec.value > 0) {{
            filtered.push_back(rec);
        }}
    }}
    return filtered;
}}
"""
    # 2. Sort function
    sort_name = f"sort_records_by_value_{file_index}"
    func_names.append(sort_name)
    file_content += f"""
void {sort_name}(std::vector<DataRecord>& records) {{
    std::sort(records.begin(), records.end(), [](const DataRecord& a, const DataRecord& b) {{
        return a.value > b.value;
    }});
}}
"""
    # 3. Aggregation function
    aggregate_name = f"calculate_category_average_{file_index}"
    func_names.append(aggregate_name)
    file_content += f"""
double {aggregate_name}(const std::vector<DataRecord>& records, int cat) {{
    double total = 0;
    int count = 0;
    for (const auto& rec : records) {{
        if (rec.category == cat) {{
            total += rec.value;
            count++;
        }}
    }}
    return (count == 0) ? 0.0 : total / count;
}}
"""
    # Main pipeline function
    pipeline_name = f"run_processing_pipeline_{file_index}"
    func_names.append(pipeline_name)
    file_content += f"""
void {pipeline_name}(std::vector<DataRecord>& initial_data) {{
    auto active_records = {filter_name}(initial_data);
    {sort_name}(active_records);
    std::cout << "Top 3 records after processing:\\n";
    for(int i=0; i < 3 && i < active_records.size(); ++i) {{
        std::cout << " ID: " << active_records[i].id << ", Val: " << active_records[i].value << std::endl;
    }}
    double avg_cat_1 = {aggregate_name}(active_records, 1);
    std::cout << "Average for category 1: " << avg_cat_1 << std::endl;
}}
"""
    file_content += f"""
int main() {{
    std::vector<DataRecord> data;
    for(int i=0; i<100; ++i) {{
        data.push_back({{i, (double)(rand() % 1000), rand() % 5, (rand() % 2 == 0)}});
    }}
    {pipeline_name}(data);
    return 0;
}}
"""
    return file_content, func_names


def generate_matrix_cpp_file(file_index):
    """Generates a file with a Matrix class and complex operations."""
    func_names = []
    class_name = f"Matrix_{file_index}"
    transpose_name = f"transpose"
    multiply_name = f"multiply"
    func_names.extend([f"{class_name}::{transpose_name}", f"{class_name}::{multiply_name}"])

    file_content = f"""#include <iostream>
#include <vector>
#include <stdexcept>

class {class_name} {{
public:
    {class_name}(int rows, int cols) : rows_(rows), cols_(cols), data_(rows * cols, 0.0) {{}}

    double& at(int r, int c) {{ return data_[r * cols_ + c]; }}
    const double& at(int r, int c) const {{ return data_[r * cols_ + c]; }}

    int get_rows() const {{ return rows_; }}
    int get_cols() const {{ return cols_; }}

    static {class_name} {transpose_name}(const {class_name}& m);
    static {class_name} {multiply_name}(const {class_name}& a, const {class_name}& b);

    void print() const {{
        for (int i = 0; i < rows_; ++i) {{
            for (int j = 0; j < cols_; ++j) {{
                std::cout << at(i, j) << "\\t";
            }}
            std::cout << std::endl;
        }}
    }}

private:
    int rows_, cols_;
    std::vector<double> data_;
}};

{class_name} {class_name}::{transpose_name}(const {class_name}& m) {{
    {class_name} result(m.cols_, m.rows_);
    for (int i = 0; i < m.rows_; ++i) {{
        for (int j = 0; j < m.cols_; ++j) {{
            result.at(j, i) = m.at(i, j);
        }}
    }}
    return result;
}}

{class_name} {class_name}::{multiply_name}(const {class_name}& a, const {class_name}& b) {{
    if (a.cols_ != b.rows_) {{
        throw std::runtime_error("Matrix dimensions are not compatible for multiplication.");
    }}
    {class_name} result(a.rows_, b.cols_);
    for (int i = 0; i < a.rows_; ++i) {{
        for (int j = 0; j < b.cols_; ++j) {{
            for (int k = 0; k < a.cols_; ++k) {{
                result.at(i, j) += a.at(i, k) * b.at(k, j);
            }}
        }}
    }}
    return result;
}}

int main() {{
    {class_name} m1(3, 4);
    for(int i=0; i<m1.get_rows(); ++i) for(int j=0; j<m1.get_cols(); ++j) m1.at(i,j) = i+j;

    {class_name} m2(4, 2);
    for(int i=0; i<m2.get_rows(); ++i) for(int j=0; j<m2.get_cols(); ++j) m2.at(i,j) = i-j;

    auto m3 = {class_name}::{multiply_name}(m1, m2);
    m3.print();
    return 0;
}}
"""
    return file_content, func_names


def generate_text_parser_file(file_index):
    """Generates a file simulating a simple config file parser."""
    func_names = []
    trim_name = f"trim_whitespace_{file_index}"
    parse_line_name = f"parse_line_{file_index}"
    load_config_name = f"load_config_{file_index}"
    func_names.extend([trim_name, parse_line_name, load_config_name])

    file_content = f"""#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <sstream>

// Helper to trim whitespace from a string
std::string {trim_name}(const std::string& str) {{
    const std::string whitespace = " \\t";
    const auto strBegin = str.find_first_not_of(whitespace);
    if (strBegin == std::string::npos) return "";
    const auto strEnd = str.find_last_not_of(whitespace);
    const auto strRange = strEnd - strBegin + 1;
    return str.substr(strBegin, strRange);
}}

// Parses a single 'key = value' line
void {parse_line_name}(const std::string& line, std::map<std::string, std::string>& config) {{
    std::stringstream ss(line);
    std::string key, value;
    if (std::getline(ss, key, '=') && std::getline(ss, value)) {{
        config[{trim_name}(key)] = {trim_name}(value);
    }}
}}

// Main function to load configuration from a simulated text block
std::map<std::string, std::string> {load_config_name}(const std::string& content) {{
    std::map<std::string, std::string> config;
    std::stringstream ss(content);
    std::string line;
    while (std::getline(ss, line)) {{
        // Ignore comments and empty lines
        if (!line.empty() && line[0] != '#') {{
            {parse_line_name}(line, config);
        }}
    }}
    return config;
}}

int main() {{
    std::string file_content = 
        "# Server Configuration\\n"
        "host = 127.0.0.1\\n"
        "port = 8080\\n"
        "user = admin\\n"
        "# Enable features\\n"
        "enable_tls = true";

    auto config = {load_config_name}(file_content);

    for (const auto& pair : config) {{
        std::cout << pair.first << " = '" << pair.second << "'\\n";
    }}
    return 0;
}}
"""
    return file_content, func_names


def main():
    """Main script to generate C++ source files and a config file for them."""
    print(f"--- Starting Step 0: Generating complex and diverse C++ source files ---")

    if os.path.exists(GENERATED_SRC_DIR):
        shutil.rmtree(GENERATED_SRC_DIR)
    os.makedirs(GENERATED_SRC_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    target_data = {}

    file_generators = [
        generate_graph_cpp_file,
        generate_data_processing_file,
        generate_matrix_cpp_file,
        generate_text_parser_file
    ]

    total_files = NUM_FILES_TO_GENERATE
    for i in range(total_files):
        generator = file_generators[i % len(file_generators)]

        file_name = f"{generator.__name__}_{i}.cpp"
        file_path = os.path.join(GENERATED_SRC_DIR, file_name)

        content, func_names = generator(i)

        with open(file_path, "w") as f:
            f.write(content)

        target_data[file_name] = func_names
        sys.stdout.write(f"\rGenerated file {i + 1}/{total_files}")
        sys.stdout.flush()

    with open(TARGET_CONFIG_PATH, 'w') as f:
        json.dump(target_data, f, indent=4)

    print(f"\n\nCode generation complete. Target function list saved to '{TARGET_CONFIG_PATH}'")


if __name__ == "__main__":
    main()