#!/usr/bin/python3
"""
    File: logger.py
    Simple Logging manager
    Date: Mon, 17/07/2023
    Author: Coolbrother
"""
import os

_OFF =0
_INFO =1
_WARN =2
_ERROR =3
_DEBUG =4
_LOG_LEVEL = _OFF
_LOG_FILE = "/tmp/zikdrum.log"
_BELL =0
_STDOUT =1
_ENDLINE =0
_WRITING_FILE =1

def init_logfile():
    """
    Removing log file at startup
    """
    
    # if _LOG_LEVEL == _OFF: return
    if not os.path.exists(_LOG_FILE): return
    os.remove(_LOG_FILE)
    print(f"Removed file: {_LOG_FILE}")

#------------------------------------------------------------------------------

def _set_logger(msg="", title="", bell=True, writing_file=False, stdout=True, endline=False):
    if _LOG_LEVEL == _OFF: return
    txt = ""
    if title: txt = f"{title}: "
    if msg: txt += f"{msg}"
    
    if _STDOUT or stdout: print(txt)
    if _BELL or bell: print("\a")
    if _WRITING_FILE or writing_file:
        # open file in append mode
        with open(_LOG_FILE, 'a') as fh:
            # _logfile.write("{}:\ {}\n".format(title, msg))
            print(txt, file=fh) 
            if _ENDLINE or endline: print("", file=fh)

#------------------------------------------------------------------------------

def set_level(level):
    global _LOG_LEVEL
    _LOG_LEVEL = level

#------------------------------------------------------------------------------

def info(msg="", title="", bell=True, writing_file=False, stdout=True, endline=False):
    level = _INFO
    if level > _LOG_LEVEL: return
    header = "[LOG_INFO]"
    title = f"{header} {title}"
    _set_logger(msg, title, bell, writing_file,  stdout, endline)

#------------------------------------------------------------------------------
def warn(msg="", title="", bell=True, writing_file=False, stdout=True, endline=False):
    level = _WARN
    if level > _LOG_LEVEL: return
    header = "[LOG_WARN]"
    title = f"{header} {title}"
    _set_logger(msg, title, bell, writing_file,  stdout, endline)

#------------------------------------------------------------------------------

def error(msg="", title="", bell=True, writing_file=False, stdout=True, endline=False):
    level = _ERROR
    if level > _LOG_LEVEL: return
    header = "[LOG_ERROR]"
    title = f"{header} {title}"
    _set_logger(msg, title, bell, writing_file,  stdout, endline)

#------------------------------------------------------------------------------


def debug(msg="", title="", bell=True, writing_file=False, stdout=True, endline=False):
    level = _DEBUG
    if level > _LOG_LEVEL: return
    header = "[LOG_DEBUG]"
    title = f"{header} {title}"
    _set_logger(msg, title, bell, writing_file,  stdout, endline)

#------------------------------------------------------------------------------

if __name__ == "__main__":
    set_level(_INFO)
    title = "Welcome"
    msg = "Hello world!"
    info(msg, title)
    msg = "First Debug message."
    debug(msg, title)
    set_level(_DEBUG)
    msg = "Second Debug message."
    debug(msg, title)
    input("It's Ok...")

#------------------------------------------------------------------------------
