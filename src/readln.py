#! /usr/bin/python3
"""
    readline wrapper for input
    Date: Thu, 26/08/2021
    Author: Coolbrother
"""
import os
import glob
from os.path import expanduser
import readline

_HISTORY_TEMPFILE = '/tmp/completer.hist'
_HISTORY_FILENAME = expanduser('~/.synth_history')
_complete_dic = {
        'list': ['files', 'directories'],
        'print': ['byname', 'bysize'],
        'stop': [],
        }

readline.set_completer_delims(' \t\n;')
readline.parse_and_bind('tab: complete')
# readline.parse_and_bind('set editing-mode vi')
# readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>?')

def list_folder(path):
    """
    Lists folder contents
    """
    if path.startswith(os.path.sep):
        # absolute path
        basedir = os.path.dirname(path)
        contents = os.listdir(basedir)
        # add back the parent
        contents = [os.path.join(basedir, d) for d in contents]
    else:
        # relative path
        contents = os.listdir(os.curdir)
    return contents

#------------------------------------------------------------------------------

def get_history_items():
    return [ readline.get_history_item(i)
             for i in range(1, readline.get_current_history_length() + 1)
             ]

#------------------------------------------------------------------------------


class BufferCompleter(object):
    def __init__(self, options):
        self.options = options
        self.current_candidates = []
        return

    #------------------------------------------------------------------------------

    def path_completion(self, text, state):
        """
        Our custom completer function
        """
        resp = None
        # print("\nPath Completion: ",text)
        
        line = readline.get_line_buffer().split()
        # print("line: ",line)
        # replace ~ with the user's home dir. See https://docs.python.org/2/library/os.path.html
        if '~' in text:
            stg = os.path.expanduser('~')
            text = text.replace('~', stg)

        # autocomplete directories with having a trailing slash
        if os.path.isdir(text):
            text += '/'
        else:
            pass

        try:
            resp = [x for x in glob.glob(text + '*')][state]
            if os.path.isdir(resp):
                resp += os.path.sep
        except IndexError:
            pass

        # print("\nresponse: ", resp)
        return resp

    #------------------------------------------------------------------------------
    
    def words_completion(self, text, state):
        """ completion from dictionarry """
        resp = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            origline = readline.get_line_buffer()
            begin = readline.get_begidx()
            end = readline.get_endidx()
            being_completed = origline[begin:end]
            words = origline.split()

            if not words:
                self.current_candidates = sorted(self.options.keys())
            else:
                try:
                    if begin == 0:
                        # first word
                        candidates = self.options.keys()
                    else:
                        # later word
                        first = words[0]
                        candidates = self.options[first]

                    if being_completed:
                        # match options with portion of input
                        # being completed
                        self.current_candidates = [ w for w in candidates
                                                    if w.startswith(being_completed) ]
                    else:
                        # matching empty string so use all candidates
                        self.current_candidates = candidates

                except (KeyError, IndexError) as err:
                    self.current_candidates = []

        try:
            resp = self.current_candidates[state]
            if len(self.current_candidates) == 1:
                resp += ' '
        except IndexError:
            resp = None
        
        # print("\nVoici response: ", resp)
        return resp

    #------------------------------------------------------------------------------
    
    def complete(self, text, state):
        words  = readline.get_line_buffer().split()
        for item in words:
            if os.path.sep in item:
                return self.path_completion(text, state)
        else:
            return self.words_completion(text, state)

    #------------------------------------------------------------------------------

#========================================

class HistoryCompleter(object):
    def __init__(self):
        self.matches = []
        return

    #------------------------------------------------------------------------------

    def hist_complete(self, text, state):
        response = None
        if state == 0:
            history_values = get_history_items()
            if text:
                self.matches = sorted(h
                                      for h in history_values
                                      if h and h.startswith(text))
            else:
                self.matches = []
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        return response

    #------------------------------------------------------------------------------

#========================================

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


def get_input(stg=""):
    return input(stg)

#------------------------------------------------------------------------------

def set_completer(dic={}):
    if not dic:
        dic = _complete_dic
    func = BufferCompleter(dic).complete
    readline.set_completer(func)

#------------------------------------------------------------------------------


def main():
    filename = _HISTORY_TEMPFILE
    # Register our completer function
    set_completer(None)
    # readline.set_completer(HistoryCompleter().complete)
    read_historyfile(filename)
    try:
        while True:
            line = get_input(">> ")
            if line == 'q':
                break
            
            if line:
                print(f"Adding {line} to the history")

    finally:
        print('Final history:', get_history_items())
        write_historyfile(filename)

#------------------------------------------------------------------------------

# Register our completer function
def _set_comp(func):
    # for test
    readline.set_completer(func)

#------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

#------------------------------------------------------------------------------
