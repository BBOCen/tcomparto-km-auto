from pathlib import Path

def create_folder(folder_path):
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    print(f"Folder: {folder_path} created")

def delete_all_files(folder_path):
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Folder '{folder_path}' does not exist.")
        return

    files_deleted = 0
    for file in folder.iterdir():
        if file.is_file():
            file.unlink()
            files_deleted += 1

    print(f"{files_deleted} file(s) deleted in '{folder_path}'")