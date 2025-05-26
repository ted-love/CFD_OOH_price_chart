import os

def find_files_with_string(root_dir, target_string):
    matching_files = []

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        if target_string in file.read():
                            matching_files.append(file_path)
                except (UnicodeDecodeError, FileNotFoundError):
                    print(f"Could not read file: {file_path}")

    return matching_files

if __name__ == "__main__":
    # Set the directory you want to search
    directory_to_search = r"C:\Users\tedlo\miniconda3\envs\live_price_chart_env\Lib\site-packages\pyqtgraph"
    search_term = "sigRangeChangedManually"

    result = find_files_with_string(directory_to_search, search_term)

    print("Files containing the string:")
    for path in result:
        print(path)
