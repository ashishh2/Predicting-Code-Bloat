import clang.cindex
import csv
import os
import sys

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "features.csv")

# This should match the TARGETS in generate_data.py
TARGETS = {
    "templates.cpp": ["process_value", "standalone_function"],
    "call_intensive.cpp": ["simple_increment", "process_data_grid"]
}

def get_features(func_cursor):
    """Extracts static analysis features for a given function cursor from the AST."""

    # 1. Is Template
    is_template = 1 if func_cursor.kind == clang.cindex.CursorKind.FUNCTION_TEMPLATE else 0

    # 2. Cyclomatic Complexity
    complexity = 1

    # 3. Call Site Count
    call_sites = 0

    # 4. Function Body Size (number of statements)
    body_stmts = 0

    # Walk through all nodes in the function's AST
    for node in func_cursor.walk_preorder():
        # Only consider nodes within the function's own body
        # FIX: SourceLocation objects cannot be compared directly.
        # Use the .offset attribute to compare their positions in the file.
        if (func_cursor.extent.start.offset <= node.extent.start.offset and
                func_cursor.extent.end.offset >= node.extent.end.offset):
            # Increment complexity for decision points
            if node.kind in [
                clang.cindex.CursorKind.IF_STMT,
                clang.cindex.CursorKind.FOR_STMT,
                clang.cindex.CursorKind.WHILE_STMT,
                clang.cindex.CursorKind.CASE_STMT,
            ]:
                complexity += 1

            # Count function calls
            if node.kind == clang.cindex.CursorKind.CALL_EXPR:
                call_sites += 1

            # Count the number of statements in the body
            if node.kind.is_statement():
                body_stmts += 1

    # The body's compound statement is counted, so subtract 1 for accuracy
    if body_stmts > 0:
        body_stmts -= 1

    return {
        "is_template": is_template,
        "cyclomatic_complexity": complexity,
        "call_site_count": call_sites,
        "body_size_stmts": body_stmts,
    }


def main():
    """Main script execution."""
    print("--- Starting Step 3: Feature Extraction from AST ---")

    try:
        index = clang.cindex.Index.create()
    except clang.cindex.LibclangError:
        print("Error: libclang library not found.")
        print("Please ensure LLVM/Clang is installed and visible in your system's PATH,")
        print("or uncomment and set the library path explicitly in this script.")
        sys.exit(1)

    features_list = []
    for filename, functions in TARGETS.items():
        source_path = os.path.join(SRC_DIR, filename)
        print(f"\nParsing source file: '{filename}'")

        # Parse the C++ file, providing the C++ standard
        tu = index.parse(source_path, args=['-std=c++17'])

        # Traverse the top-level nodes of the AST
        for cursor in tu.cursor.get_children():
            # Check if the node is a function we are targeting
            if cursor.spelling in functions and cursor.is_definition():
                print(f"  Extracting features for: '{cursor.spelling}'")
                func_features = get_features(cursor)
                func_features["function_name"] = cursor.spelling
                func_features["file_name"] = filename
                features_list.append(func_features)
                print(f"    -> Features: {func_features}")

    # Write all features to a CSV file
    if features_list:
        fieldnames = ["function_name", "file_name", "is_template", "cyclomatic_complexity", "call_site_count",
                      "body_size_stmts"]
        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(features_list)
        print(f"\nFeature extraction complete. Results saved to '{OUTPUT_CSV}'")
    else:
        print("\nNo features were extracted. Please check the source files and TARGETS configuration.")


if __name__ == "__main__":
    main()