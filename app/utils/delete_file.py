import os

def delete_file(filename: str | None, folder: str):
    if not filename or not folder: return

    full_path = os.path.join("media", "uploads", folder, filename)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
    except OSError:
        pass


def cleanup(saved_paths):
    for path in saved_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass