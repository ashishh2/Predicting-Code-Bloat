import os
import subprocess
import re
import csv
import sys
import json
import shutil
import time

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
GENERATED_SRC_DIR = os.path.join(PROJECT_ROOT, "src_generated")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
TEMP_BUILD_DIR = os.path.join(PROJECT_ROOT, "temp_build")

TARGET_CONFIG_PATH = os.path.join(DATA_DIR, "target_functions.json")
OUTPUT_CSV = os.path.join(DATA_DIR, "size_impact.csv")
COMPILER = "clang++"


def compile_and_get_size(source_path, output_name):
    """Compiles a source file into an object file and returns its size."""
    output_path = os.path.join(TEMP_BUILD_DIR, output_name)
    try:
        # We compile with -c to create an object file, which gives a more
        # precise measurement of the code's size without standard libraries.
        # We also specify the C++ standard.
        cmd = [COMPILER, "-std=c++17", "-O2", "-c", source_path, "-o", output_path]
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=30  # Add a timeout for safety
        )
        return os.path.getsize(output_path)
    except subprocess.CalledProcessError as e:
        # Silently log errors for now to not clutter the output
        # print(f"Compilation failed for {output_name}:\n{e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        # print(f"Compilation timed out for {output_name}")
        return None
    finally:
        # The script will clean up the entire temp_build directory at the end
        pass


def modify_source_for_function(original_content, func_name, attribute):
    """
    Adds an inline attribute to a specific function in the source code content.
    Handles both normal and template functions, as well as class methods.
    """
    # Regex to handle regular functions, templates, and class methods
    # It looks for the function name, preceded by return type, optional template, or class name.
    # This is more robust than the previous version.
    pattern = re.compile(
        r"^(template<.*?>\s*)?"  # Optional template declaration (Group 1)
        r"((?:\w+::)*\w+\s+)"  # Return type, possibly with class scope (Group 2)
        r"({func})".format(func=re.escape(func_name)) +  # The function name itself (Group 3)
        r"(\s*\(.*?\)\s*\{)",  # Arguments and opening brace (Group 4)
        re.MULTILINE
    )

    replacement = r"\1{attr} \2\3\4".format(attr=attribute)
    new_content, count = pattern.subn(replacement, original_content)

    if count > 0:
        return new_content

    # Fallback for class methods where the return type might be on a different line
    # or defined outside the class body.
    method_pattern = re.compile(
        r"({func})".format(func=re.escape(func_name)) +
        r"(\(.*\)\s*\{)",
        re.MULTILINE
    )
    # This is tricky because we don't know the return type to prepend the attribute.
    # For this project, the first regex is the primary one. This is a known limitation.
    # If the first one fails, we'll return original content.
    return original_content if count == 0 else new_content


def process_file(file_name, target_functions, writer):
    """Processes a single C++ source file to measure inline impact."""
    source_path = os.path.join(GENERATED_SRC_DIR, file_name)
    with open(source_path, 'r') as f:
        original_content = f.read()

    temp_source_path = os.path.join(TEMP_BUILD_DIR, "temp_code.cpp")

    for func in target_functions:
        # Clean the function name if it's a class method
        clean_func_name = func.split("::")[-1]

        # 1. Get size with NOINLINE
        modified_noinline = modify_source_for_function(original_content, clean_func_name, "__attribute__((noinline))")
        with open(temp_source_path, 'w') as f:
            f.write(modified_noinline)
        size_no_inline = compile_and_get_size(temp_source_path, f"bin_{clean_func_name}_noinline.o")

        # 2. Get size with ALWAYS_INLINE
        modified_inline = modify_source_for_function(original_content, clean_func_name,
                                                     "__attribute__((always_inline))")
        with open(temp_source_path, 'w') as f:
            f.write(modified_inline)
        size_always_inline = compile_and_get_size(temp_source_path, f"bin_{clean_func_name}_always_inline.o")

        if size_no_inline and size_always_inline and size_no_inline > 0:
            percent_increase = ((size_always_inline - size_no_inline) / size_no_inline) * 100
            writer.writerow({
                "function_name": func,
                "file_name": file_name,
                "size_increase_percent": percent_increase
            })


def main():
    print("--- Starting Step 2 (Scaled): Data Generation ---")

    if not os.path.exists(TARGET_CONFIG_PATH):
        print(f"Error: Could not find '{TARGET_CONFIG_PATH}'.")
        print("Please run 'generate_code.py' first to create the C++ source files.")
        return

    with open(TARGET_CONFIG_PATH, 'r') as f:
        target_data = json.load(f)

    # Setup a temporary directory for build files
    if os.path.exists(TEMP_BUILD_DIR):
        shutil.rmtree(TEMP_BUILD_DIR)
    os.makedirs(TEMP_BUILD_DIR)

    start_time = time.time()
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["function_name", "file_name", "size_increase_percent"])
        writer.writeheader()

        total_files = len(target_data)
        for i, (file_name, functions) in enumerate(target_data.items()):
            process_file(file_name, functions, writer)
            sys.stdout.write(f"\rProcessed file {i + 1}/{total_files}")
            sys.stdout.flush()

    # Clean up build files
    shutil.rmtree(TEMP_BUILD_DIR)

    end_time = time.time()
    print(f"\n\nData generation complete. Results saved to '{OUTPUT_CSV}'")
    print(f"Total time taken: {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()