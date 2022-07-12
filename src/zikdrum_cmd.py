#! /usr/bin/env python3
"""
    File: zikdrum_cmd.py
    See changelog

    Date: Tue, 12/07/2022
    Author:
    Coolbrother
"""

import os, sys
import readline
import interfaceapp as intapp


_HISTORY_TEMPFILE = "/tmp/.synth_history"

def read_historyfile(filename=""):
    if not filename:
        filename = _HISTORY_FILENAME
    if os.path.exists(filename):
        readline.read_history_file(filename)
        # print('Max history file length:', readline.get_history_length())
        # print('Startup history:', get_history_items())

#------------------------------------------------------------------------------

def write_historyfile(filename=""):
    # print('Final history:', get_history_items())
    if not filename:
        filename = _HISTORY_FILENAME
    readline.write_history_file(filename)

#------------------------------------------------------------------------------


class CommandApp(object):
    def __init__(self):
        self.iap = None
        self.notifying =0
        self.filename = "/home/com/banks/sf2/FluidR3_GM.sf2"
        # self.filename = "/home/banks/sf2/Yamaha_XG_Sound_Set.sf2"
        # not work with fluidsynth 1.1.6
        # self.filename = "/home/banks/sf2/OmegaGMGS.sf2"
        self.msg_home = "Grovit Synth..."

    #-------------------------------------------
    
    def display(self, msg=""):
        print(msg)
    
    #-------------------------------------------

    def display_status(self, msg=""):
        print("Status: ", msg)
    
    #-------------------------------------------

    def notify(self, msg):
        """
        receive notification
        from MainApp object
        """

        if self.notifying:
            self.display(msg)

    #-------------------------------------------

    
    def test(self):
        """
        test function
        from MainApp object
        """
        self.display("Test Functions")
        self.iap.test_synth_engine()
        # testing track 1
        tracknum =1
      
    #------------------------------------------------------------------------------
   
    def beep(self):
        """
        Generate beep
        from CommandApp object
        """

    #------------------------------------------------------------------------------
        
        print("\a")
    def main(self, midi_filename="", audio_device=""):
        """ 
        main function 
        from MainApp object
        """

        filename = _HISTORY_TEMPFILE
        read_historyfile(filename)

        audio_device = "hw:1"
        self.iap = intapp.InterfaceApp(self)
        self.notifying =1
        self.iap.init_app(midi_filename, audio_device)
        print("\a")
        
        try:
            while 1:
                key = param1 = param2 = ""
                valStr = input("-> ")
                if valStr == '': valStr = savStr
                else: savStr = valStr
                if valStr == " ":
                    key = valStr
                else:
                    lst = valStr.split()
                    lenLst = len(lst)
                    if lenLst >0: key = lst[0]
                    if lenLst >1: param1 = lst[1]
                    if lenLst >2: param2 = lst[2]

                if key == 'Q':
                    print("Bye Bye!!!")
                    self.iap.close_app()
                    self.beep()
                    break
                elif key == 'T': # for test
                    self.test()
        finally:
            write_historyfile(filename)

    #-------------------------------------------

#========================================

if __name__ == "__main__":
    midi_filename = ""
    audio_device = "" # hw:0 by default
    app = CommandApp()
    if len(sys.argv) >= 2:
        midi_filename = sys.argv[1]
    if len(sys.argv) >= 3:
        audio_device = sys.argv[2]
        # print("voici filename", filename)
    app.main(midi_filename, audio_device)
    

#------------------------------------------------------------------------------
