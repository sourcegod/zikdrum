#python3
"""
    File: utils.py
    Module for miscellaneous functions.
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""

DEBUG=1
_logfile = None

def debug(msg="", title="", bell=True, write_file=False, stdout=True, endline=False):
    if DEBUG:
        if stdout:
            txt = ""
            if title and not msg:
                txt = "{}".format(title)
            elif msg and not title:
                txt = "{}".format(msg)
            elif msg and title:
                txt = "{}: {}".format(title, msg)
            print(txt)

        if bell:
            # curses.beep()
            print("\a")
        if write_file:
            with open('/tmp/zikdrum.log', 'a') as fh:
                # _logfile.write("{}:\ {}\n".format(title, msg))
                txt = ""
                if title and not msg:
                    txt = "{}:".format(title)
                elif msg and not title:
                    txt = "{}".format(msg)
                elif title and msg:
                    txt = "{}:\n{}".format(title, msg)

                print(txt, file=fh) 

                if endline:
                    print("", file=fh)

#------------------------------------------------------------------------------

def beep():
    # curses.beep()
    print("\a")

#-------------------------------------------

def limit_value(val, min_val=0, max_val=127):
    """ limit value """
    
    if val < min_val: val = min_val
    elif val > max_val: val = max_val
    
    return val

#-------------------------------------------


