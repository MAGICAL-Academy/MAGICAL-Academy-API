import os


def aggregate_python_files(root_dir, output_file):
    # Initialize an empty string to store all the content
    all_content = ""

    # Walk through all directories and files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)

                # Add a header for each file
                all_content += f"\n\n# File: {file_path}\n\n"

                # Read and append the content of the file
                with open(file_path, 'r', encoding='utf-8') as file:
                    all_content += file.read()

    # Write all content to the output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write(all_content)

    print(f"All Python files have been aggregated into {output_file}")


if __name__ == "__main__":
    # Set the root directory to the current directory
    root_directory = "."

    # Set the output file name
    output_filename = "aggregated_python_files.txt"

    # Run the aggregation function
    aggregate_python_files(root_directory, output_filename)