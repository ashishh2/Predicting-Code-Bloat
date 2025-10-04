import clang.cindex
import csv
import os
import json
import sys
import time
import subprocess

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
GENERATED_SRC_DIR = os.path.join(PROJECT_ROOT, "src_generated")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TARGET_CONFIG_PATH = os.path.join(DATA_DIR, "target_functions.json")
OUTPUT_CSV = os.path.join(DATA_DIR, "features.csv")


# --- Find and set libclang path ---
def find_and_set_libclang_path():
    """Dynamically finds and sets the path to the libclang library."""
    if sys.platform == 'darwin':  # macOS
        try:
            llvm_prefix = subprocess.check_output(['brew', '--prefix', 'llvm']).decode('utf-8').strip()
            libclang_path = os.path.join(llvm_prefix, 'lib')
            if os.path.exists(os.path.join(libclang_path, 'libclang.dylib')):
                clang.cindex.Config.set_library_path(libclang_path)
                print(f"Successfully set libclang path to: {libclang_path}")
                return
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("Warning: 'brew' command not found or 'llvm' not installed via Homebrew.")
    print("Info: Relying on default library search paths for libclang.")


find_and_set_libclang_path()


def get_features(func_cursor, translation_unit):
    """Extracts a revised and more robust set of features for a function."""
    # --- Feature Initialization ---
    complexity = 1
    body_stmts = 0
    local_vars = 0

    # NEW Feature: Token Count
    # A very reliable measure of the function's physical size.
    tokens = translation_unit.get_tokens(extent=func_cursor.extent)
    token_count = len(list(tokens))

    # NEW Feature: Is Complex Return Type
    # Checks if the function returns something more complex than a basic type.
    return_type = func_cursor.result_type.spelling
    simple_types = ['void', 'int', 'float', 'double', 'char', 'bool', 'short', 'long']
    is_complex_return = 1 if not any(st in return_type for st in simple_types) else 0

    # Feature: Parameter Count
    parameter_count = len(list(func_cursor.get_arguments()))

    func_start = func_cursor.extent.start.offset
    func_end = func_cursor.extent.end.offset

    for node in func_cursor.walk_preorder():
        if not (func_start <= node.extent.start.offset and node.extent.end.offset <= func_end):
            continue

        # --- Cyclomatic Complexity ---
        if node.kind in [
            clang.cindex.CursorKind.IF_STMT, clang.cindex.CursorKind.FOR_STMT,
            clang.cindex.CursorKind.WHILE_STMT, clang.cindex.CursorKind.CASE_STMT,
            clang.cindex.CursorKind.CONDITIONAL_OPERATOR,
        ]:
            complexity += 1

        # Feature: Local Variable Count
        if node.kind == clang.cindex.CursorKind.VAR_DECL:
            local_vars += 1

        # --- Body Size (Statement Count) ---
        if node.kind.is_statement() and node.kind != clang.cindex.CursorKind.COMPOUND_STMT:
            body_stmts += 1

    return {
        "cyclomatic_complexity": complexity,
        "parameter_count": parameter_count,
        "local_variable_count": local_vars,
        "body_size_stmts": body_stmts,
        "token_count": token_count,
        "is_complex_return": is_complex_return,
    }


def find_function_cursor(cursor, target_func_name):
    """Recursively search for a function or method cursor by name."""
    if "::" in target_func_name:
        parts = target_func_name.split("::")
        class_name, method_name = parts[0], parts[1]

        for child in cursor.get_children():
            if child.kind in [clang.cindex.CursorKind.CLASS_DECL,
                              clang.cindex.CursorKind.STRUCT_DECL] and child.spelling == class_name:
                for method in child.get_children():
                    if method.kind == clang.cindex.CursorKind.CXX_METHOD and method.spelling == method_name:
                        return method
        return None

    for child in cursor.get_children():
        if child.kind in [clang.cindex.CursorKind.FUNCTION_DECL,
                          clang.cindex.CursorKind.FUNCTION_TEMPLATE] and child.spelling == target_func_name:
            return child
    return None


def main():
    print("--- Starting Step 2 (Scaled): Feature Extraction from AST ---")

    if not os.path.exists(TARGET_CONFIG_PATH):
        print(f"Error: Could not find '{TARGET_CONFIG_PATH}'. Please run 'generate_code.py' first.")
        return

    with open(TARGET_CONFIG_PATH, 'r') as f:
        target_data = json.load(f)

    try:
        index = clang.cindex.Index.create()
    except clang.cindex.LibclangError as e:
        print(f"\nFATAL: libclang library not found. Please run 'brew install llvm'.\nOriginal error: {e}")
        return

    all_features = []
    start_time = time.time()
    total_files = len(target_data)

    for i, (file_name, functions) in enumerate(target_data.items()):
        source_path = os.path.join(GENERATED_SRC_DIR, file_name)
        if not os.path.exists(source_path): continue

        tu = index.parse(source_path, args=['-std=c++17'])

        for func_name in functions:
            cursor = find_function_cursor(tu.cursor, func_name)
            if cursor:
                # Pass the translation unit (tu) to the get_features function
                func_features = get_features(cursor, tu)
                func_features["function_name"] = func_name
                func_features["file_name"] = file_name
                all_features.append(func_features)

        sys.stdout.write(f"\rParsed file {i + 1}/{total_files}")
        sys.stdout.flush()

    # **UPDATED**: New fieldnames for the CSV file
    fieldnames = [
        "function_name", "file_name", "cyclomatic_complexity", "parameter_count",
        "local_variable_count", "body_size_stmts", "token_count", "is_complex_return"
    ]
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_features)

    end_time = time.time()
    print(f"\n\nFeature extraction complete. Results saved to '{OUTPUT_CSV}'")
    print(f"Total time taken: {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()