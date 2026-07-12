import os

def delete_file(filename: str | None):
    if not filename: return
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except OSError:
        pass


def delete_files(filenames):
    if filenames == []: return
    
    for filename in filenames:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except OSError:
            pass