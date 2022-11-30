import os


def root_path(*args):
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", *args))
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def project_path(*args):
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "..", *args))
