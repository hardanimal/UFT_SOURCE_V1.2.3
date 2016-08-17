import sys
sys.path.append('src')
from cx_Freeze import setup, Executable

includes = ["atexit", "UFT", "UFT_GUI"]
include_files = [('src/UFT/devices/aardvark/aardvark32.so', 'aardvark32.so'),
                 ('src/UFT/devices/aardvark/aardvark64.so', 'aardvark64.so'),
                 ('src/UFT/devices/aardvark/aardvark32.pyd', 'aardvark32.pyd'),
                 ('src/UFT/devices/aardvark/aardvark64.pyd', 'aardvark64.pyd'),
                 ]
#bin_includes = ['src/aardvark32.so', 'src/aardvark64.so']

if sys.platform == "win32":
    base = "Win32GUI"
else:
    base = None

exe = Executable(script="src/UFT_GUI/main.py", base=base)

setup(
    name="UFT Test Executive",
    version="1.2",
    options={"build_exe": {"includes": includes,
                           "include_files": include_files,
                           #"bin_includes": bin_includes,
                           #"path": sys.path + ['src'],
                           }
             },
    executables=[exe],
    )
