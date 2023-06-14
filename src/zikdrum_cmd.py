#! /usr/bin/env python3
"""
    File: zikdrum_cmd.py
    See changelog

    Date: Tue, 12/07/2022
    Author:
    Coolbrother
"""

import os, sys
import interfaceapp as intapp
import readln

_help = """ Help on Zikdrum
  b: forward
  k: toggle click
  h, ?: print this help
  l: toggle loop
  p, t, space: toggle play pause
  q, Q: quit
  r: toggle record
  R: toggle record mode (replace, mix)
  v: stop
  w: rewind
  x: toggle mute
  <: goto start
  >: goto end

  bpm VAL: set bpm
  sta, status: display player status and position in secs
  demo, test: testing

"""

def debug(msg="", title="", bell=True):
    if _DEBUG:
        if title: msg = f"{title}: {msg}"
        print(msg)
        if bell: print("\a")
    
#------------------------------------------------------------------------------

def beep():
    print("\a")

#-------------------------------------------



class CommandApp(object):
    def __init__(self):
        self.iap = intapp.InterfaceApp(self)
        self.notifying =0
        self.filename = "/home/com/banks/sf2/FluidR3_GM.sf2"
        # self.filename = "/home/banks/sf2/Yamaha_XG_Sound_Set.sf2"
        # not work with fluidsynth 1.1.6
        # self.filename = "/home/banks/sf2/OmegaGMGS.sf2"
        self.msg_home = "Grovit Synth..."
        self._exclu_func = [
                "quit", "panic", "test_synth_engine", 
                "open_file", "new_player",
        ]
        
        # global dict
        self._global_dic = {
                ("demo", "test"): self.iap.test_synth_engine,
                (".", "panic"): self.iap.panic,
        }
        
        # info dictt
        self._info_dic = {
                ("info", ): self.iap.print_info,
                ("u", "sta", "status"): self.iap.print_status,
                ("bar", ): self.iap.get_bar,
                ("bpm", ): self.iap.change_bpm,
        }

        # file dict
        self._file_dic = {
                ("new", ): self.iap.new_player,
                ("open", ): self.iap.open_file,
        }

        # transport dict
        self._transport_dic = {
                (" ", "pp", "play"): self.iap.play_pause,
                ("st", "stop"): self.iap.stop,
                ("w", "rw", "rewind"): self.iap.rewind,
                ("b", "fw", "forward"): self.iap.forward,
                ("<", "gos", "gotostart"): self.iap.goto_start,
                (">", "goe", "gotoend"): self.iap.goto_end,
                ("gob", "gotobar"): self.iap.goto_bar,
        }

        # dict list
        self._com_lst = [
                self._global_dic,
                self._info_dic,
                self._file_dic,
                self._transport_dic,
        ]

    #-------------------------------------------
    
    def display(self, msg=""):
        print('\r', msg)
    
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

    def beep(self):
        """
        Generate beep
        from CommandApp object
        """
        
        print("\a")

    #------------------------------------------------------------------------------
    
    def check_func_allowed(self, funcName):
        """
        check whether function can be called or not.
        Specially when the player is not ready.
        from CommandApp object
        """
        
        """
        if not self.iap.player_is_ready() and\
                funcName not in self._exclu_func:
                    msg = "Error Command: player is not ready."
                    self.display(msg)
                    return False
        """


        return True

    #------------------------------------------------------------------------------
    
    def search_func(self, funcName):
        """
        search function from dict list
        returns function
        from CommandApp object
        """
        cmdFunc = None
        for dic in self._com_lst:
            for keys in dic.keys():
                # keys are tuple
                if funcName in keys:
                    cmdFunc = dic[keys]
                    # print("cmdFunc found: ", cmdFunc.__name__)
                    return cmdFunc

        return cmdFunc

    #------------------------------------------------------------------------------

    def parse_string(self, val_str, *args):

        # print(f"Parsing: ", val_str)
        
        cmdFunc = None
        funcName = ""
        # Remove all spaces from string
        if val_str:
            argLst = val_str.split()
        else:
            argLst = args
        if argLst:
            funcName = argLst.pop(0).lower()
            cmdFunc = self.search_func(funcName)
            if cmdFunc: 
                if self.check_func_allowed(cmdFunc.__name__):
                    cmdFunc(*argLst)
                else:
                    return
            else: # not cmdFunc
                msg = f"{funcName}: command not found."
                self.display(msg)

            
    #------------------------------------------------------------------------------
    
  
    def main(self, midi_filename="", audio_device=""):
        """ 
        main function 
        from MainApp object
        """

        # Register our completer function
        # readln.set_completer(_words_dic)
        readln.read_historyfile()

        if not audio_device:
            audio_device = "hw:1"
            audio_device = "plughw:1"
        if self.iap:
            self.notifying =1
            self.iap.init_app(midi_filename, audio_device)
            print("\a")
            sav_str = ""
            
        try:
            while 1:
                key = val_str = ""
                val_str = input("\r-> ")
                if val_str == '': val_str = sav_str
                else: sav_str = val_str
                if val_str == " ": val_str = "pp"
                key = val_str

                if key in ('q', 'Q'):
                    print("Bye Bye!!!")
                    if self.iap: self.iap.close_app()
                    self.beep()
                    break
                elif key in ('?', 'h',):
                    self.display(_help)

                elif key == 'T': # for test
                    self.test()
                else:
                    self.parse_string(val_str)
        
        finally:
            readln.write_historyfile()

    #-------------------------------------------
    
    def test(self):
        """
        test function
        from CommandApp object
        """
        
        self.iap.test()
        """
        self.display("Test Functions")
        self.iap.test_synth_engine()
        # testing track 1
        tracknum =1
        """
      
    #------------------------------------------------------------------------------
 
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
