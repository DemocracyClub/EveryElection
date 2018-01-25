import tempfile
import zipfile


def unzip(filepath):
    zip_file = zipfile.ZipFile(filepath, 'r')
    tmpdir = tempfile.mkdtemp()
    zip_file.extractall(tmpdir)
    return tmpdir
