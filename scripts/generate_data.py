import os
import subprocess
import re
import csv
import sys

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "size_impact.csv")
TEMP_BUILD_DIR = os.path.join(PROJECT_ROOT, "temp_build")

COMPILER = "clang++"

# Updated to target the new high-impact C++ files and functions
TARGETS = {
    "templates.cpp": ["process_value", "standalone_function"],
    "call_intensive.cpp": ["simple_increment", "process_data_grid"]
}


def compile_and_get_size(source_file, output_path):
    """
    Compiles a source file to an object file (-c) and returns its size.
    Measuring the object file is more sensitive than measuring the final executable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        # The '-c' flag tells the compiler to stop after compilation,
        # producing an object file (.o) without linking.
        command = [COMPILER, "-std=c++17", "-O2", "-c", source_file, "-o", output_path]
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        return os.path.getsize(output_path)
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation for {os.path.basename(output_path)}:")
        print(e.stderr)
        return None


def modify_source_for_function(original_content, func_name, attribute):
    """Adds a compiler attribute to a specific function or function template."""
    # Regex for templates: Captures the template declaration and the function
    # signature in two separate groups to correctly insert the attribute.
    pattern_template = re.compile(
        rf"(template<.*?>\s+)((?:void|int)\s+{re.escape(func_name)}\s*\(.*?\))\s*{{",
        re.DOTALL
    )
    # Regex for regular functions
    pattern_regular = re.compile(
        rf"((?:void|int)\s+{re.escape(func_name)}\s*\(.*?\))\s*{{",
        re.DOTALL
    )

    # For templates, insert the attribute between group 1 and group 2
    replacement_template = f"\\1 {attribute} \\2 {{"
    # For regular functions, prepend the attribute to the whole signature
    replacement_regular = f"{attribute} \\1 {{"

    # Try to match a template first
    new_content, count = re.subn(pattern_template, replacement_template, original_content, count=1)
    if count == 0:
        # If not a template, try matching a regular function
        new_content, count = re.subn(pattern_regular, replacement_regular, original_content, count=1)

    if count == 0:
        raise RuntimeError(f"Could not find function or template '{func_name}' to modify.")
    return new_content


def main():
    """Main script execution."""
    print("--- Starting Step 2: Data Generation with High-Impact Scenarios ---")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(TEMP_BUILD_DIR, exist_ok=True)

    results = []

    for filename, functions in TARGETS.items():
        source_path = os.path.join(SRC_DIR, filename)
        print(f"\nProcessing source file: '{filename}'")

        try:
            with open(source_path, "r") as f:
                original_content = f.read()
        except FileNotFoundError:
            print(f"  -> Error: Source file not found at '{source_path}'. Skipping.")
            continue

        for func in functions:
            print(f"  Analyzing function: '{func}'...")
            temp_source_path = os.path.join(TEMP_BUILD_DIR, "temp_code.cpp")

            try:
                # 1. Get size with NOINLINE
                modified_noinline = modify_source_for_function(original_content, func, "__attribute__((noinline))")
                with open(temp_source_path, "w") as f:
                    f.write(modified_noinline)
                size_no_inline = compile_and_get_size(temp_source_path,
                                                      os.path.join(TEMP_BUILD_DIR, f"bin_{func}_noinline.o"))

                # 2. Get size with ALWAYS_INLINE
                modified_always_inline = modify_source_for_function(original_content, func,
                                                                    "__attribute__((always_inline))")
                with open(temp_source_path, "w") as f:
                    f.write(modified_always_inline)
                size_always_inline = compile_and_get_size(temp_source_path,
                                                          os.path.join(TEMP_BUILD_DIR, f"bin_{func}_always_inline.o"))

                # 3. Calculate impact
                if size_no_inline is not None and size_always_inline is not None and size_no_inline > 0:
                    percent_increase = ((size_always_inline - size_no_inline) / size_no_inline) * 100
                    print(
                        f"    -> No-inline: {size_no_inline} bytes, Always-inline: {size_always_inline} bytes, Impact: {percent_increase:.2f}%")
                    results.append({
                        "function_name": func,
                        "file_name": filename,
                        "size_increase_percent": percent_increase
                    })
                else:
                    print(f"    -> Could not calculate impact for '{func}'.")

            except Exception as e:
                print(f"    -> An error occurred while processing '{func}': {e}")

    # Write results to CSV
    if results:
        fieldnames = ["function_name", "file_name", "size_increase_percent"]
        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nData generation complete. Results saved to '{OUTPUT_CSV}'")
    else:
        print("\nNo data was generated. Please check for compilation errors.")

    # Clean up
    for file_name in os.listdir(TEMP_BUILD_DIR):
        os.remove(os.path.join(TEMP_BUILD_DIR, file_name))
    os.rmdir(TEMP_BUILD_DIR)
    print("Temporary build files cleaned up.")


if __name__ == "__main__":
    main()