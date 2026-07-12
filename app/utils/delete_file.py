import os

def delete_file(filename: str | None):
    if not filename: return
    
    filename = filename.lstrip("/")
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except OSError:
        pass


def delete_files(filenames):
    if not filenames: return
    
    for filename in filenames:
        filename = filename.lstrip("/")
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except OSError:
            pass