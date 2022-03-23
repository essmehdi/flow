import re
import math

def convert_size(size):
    if size == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(size, 1024)))
    unit = math.pow(1024, index)
    result = round(size / unit, 2)
    return f"{result} {size_names[index]}"

def get_filename_from_url(url):
    from urllib.parse import unquote
    filename = unquote(url).split("/")[-1]
    if len(filename) >= 200:
        filename = filename[-1:-100:-1].strip()
    return filename

def get_eta(speed, size):
    if speed > 0:
        eta = size // speed
        seconds = eta % 60
        minutes = (eta // 60) % 60
        hours = eta // 3600
        return f"{hours}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"
    return ""

def file_extension_match(filename, extensions):
    extensions_regex = "(?:" + extensions.strip().replace('.', '\.').replace(' ', '|') + ")$"
    return False if re.search(extensions_regex, filename) is None else True
