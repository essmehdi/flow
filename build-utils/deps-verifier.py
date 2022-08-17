import sys

try:
    import pycurl
except ImportError:
    print("Make sure you have installed 'pycurl' for Python.")
    sys.exit(1)

try:
    import validators
except ImportError:
    print("Make sure you have installed 'validators' for Python.")
    sys.exit(1)
