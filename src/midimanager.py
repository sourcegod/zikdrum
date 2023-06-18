#!/usr/bin/python3
"""
    File: midimanager.py:
    Module midi device and FluidSynth manager 
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""

import time
import fluidsynth
import mido
from constants import * # for patch_lst


class MidiFluid(object):
    """ fluidsynth manager """
    def __init__(self):
        self.fs = None
        self.sfid = None

    #-----------------------------------------
    
    def init_synth(self, filename, audio_out=""):
        """
        init Fluidsynth
        from MidiFluid object
        """

        if not audio_out:
            audio_out = "hw:0" # for default audio device
        # increasing gain for more audio output volume
        # default: 0.2
        audio_driver = "alsa"
        
        # audio_out = "sysdefault"
        # audio_out = "hw:0"
        # audio_out = "hw:1"
        gain =3
        gain=1
        self.fs = fluidsynth.Synth(gain=gain)
        self.fs.start(driver=audio_driver, device=audio_out)
        # print(f"voici filename: {filename}")
        filename = "/home/com/banks/sf2/fluidr3_gm.sf2"
        self.sfid = self.fs.sfload(filename, update_midi_preset=0)
        # chan, sfid, bank, preset
        # bank select 128 for percussion
        self.fs.program_select(0, self.sfid, 0, 0)
        # self.fs.bank_select(0, 128)

    #-----------------------------------------

    def close_synth(self):
        """ 
        close fluidsynth 
        """
        if self.fs:
            self.fs.delete()

    #-----------------------------------------
    
    def is_active(self):
        """
        returns FluidSynth active
        from MidiFluid object
        """

        return self.fs

    #-----------------------------------------

    def program_change(self, chan, program):
        """
        Send program change to FluidSynth
        from MidiFluid object
        """

        if self.fs is None: return
        self.fs.program_change(chan, program)

    #-----------------------------------------

    def note_on(self, chan, note, vel):
        """
        send note on to FluidSynth
        from MidiFluid object
        """

        if self.fs is None: return
        self.fs.noteon(chan, note, vel)
    
    #-----------------------------------------
 
    def note_off(self, chan, note):
        """
        send note off to FluidSynth
        from MidiFluid object
        """

        if self.fs is None: return
        self.fs.noteoff(chan, note)
    
    #-----------------------------------------


#========================================

class GenericSynth(object):
    """ External Synth Manager  """
    def __init__(self):
        self._chan =0
        self._midi_out = None
        self._outport_num =0

    #-----------------------------------------
    
    def init_synth(self, outport_num=None):
        """
        init GenericSynth
        from GenericSynth object
        """

        if outport_num is None:
            outport_num = self._outport_num
        self.open_output(outport_num)

    #-----------------------------------------

    def close_synth(self):
        """ 
        close GenericSynth 
        """
        
        self._midi_out = None

    #-----------------------------------------

    
    def open_output(self, port_num=0):
        """
        open Midi Output Port
        from GenericSynth object
        """

        output_names = mido.get_output_names()
        try:
            port_name = output_names[port_num]
            self._midi_out = mido.open_output(port_name)
            self._outport_num = port_num
            self._outport_name = port_name
        except IndexError:
            print(f"Error opening midi output Port {port_num}")
            self._midi_out = None
        
        return self._midi_out

    #-----------------------------------------
    
    def is_active(self):
        """
        returns FluidSynth active
        from GenericSynth object
        """

        return self._midi_out

    #-----------------------------------------

    def program_change(self, chan, program):
        """
        set program change
        from GenericSynth object
        """
        
        # No test for performance
        msg = mido.Message(type='program_change')
        msg.channel = chan
        msg.program = program
        self._midi_out.send(msg)
        self._chan = chan

    #-----------------------------------------

    def note_on(self, chan, note, vel):
        """
        set Note On
        from GenericSynth object
        """
        
        # No test for performance
        msg = mido.Message(type='note_on')
        msg.channel = chan
        msg.note = note
        msg.velocity = vel
        self._midi_out.send(msg)
        self._chan = chan

    #-----------------------------------------

    def note_off(self, chan, note):
        """
        set Note Off
        from MidiManager object
        """
        
        # No test for performance
        msg = mido.Message(type='note_off')
        msg.channel = chan
        msg.note = note
        self._midi_out.send(msg)

    #-----------------------------------------


#========================================



class MidiManager(object):
    """ Midi manager from mido module """
    def __init__(self, parent=None):
        self.parent = parent
        self._synth_type =0
        self._synth_obj = None
        self.chan =0
        self._midi_in = None
        self._midi_out = None
        self._inport_num =0
        self._inport_name = ""
        self._outport_num =0
        self._outport_name = ""
        self._audio_out = "hw:0"

    #-----------------------------------------

    def init_midi(self, inport_num=0, outport_num=0, synth_type=0, bank_filename="", audio_out=""):
        """
        init synth 
        from MidiManager object
        """

        if synth_type is None:
            synth_type = self._synth_type
        else:
            self._synth_type = synth_type
        if inport_num is None:
            inport_num = self._inport_num
        else:
            self._inport_num = inport_num

        if outport_num is None:
            outport_num = self._outport_num
        else:
            self._outport_num = outport_num

        if audio_out is None:
            audio_out = self._audio_out
        else:
            self._audio_out = audio_out


        if self._synth_type == 0:
            self._synth_obj = GenericSynth()
            self._synth_obj.init_synth(outport_num)
        else:
            self.close_midi()
            self._synth_obj = MidiFluid()
            self._synth_obj.init_synth(bank_filename, audio_out)
        # set channel 9 for drum percussion

    #-----------------------------------------

    def close_midi(self):
        if self._synth_type == 0:
            self._synth_obj = None
        elif self._synth_type == 1:
            if self._synth_obj:
                self._synth_obj.close_synth()
                self._synth_obj = None

        self._midi_in = None
        self._midi_out = None

    #-----------------------------------------

    def print_ports(self):
        """
        print input and output ports through mido driver
        from MidiManager object
        """

        print("Input Midi Ports:")
        names = mido.get_input_names()
        for (i, item) in enumerate(names): print(f"{i}: {item}")
        
        print("Output Midi Ports:")
        names = mido.get_output_names()
        for (i, item) in enumerate(names): print(f"{i}: {item}")

    #-----------------------------------------

    def get_in_ports(self):
        return mido.get_input_names()

    #-----------------------------------------

    def get_out_ports(self):
        return mido.get_output_names()

    #-----------------------------------------

    def send_to(self, msg, out_port=0):
        output_names = mido.get_output_names()
        try:
            port_name = output_names[out_port]
            self._outport_num = out_port
        except IndexError:
            print(f"Error: cannot open Midi Output Port : {out_port}")
        midi_out = mido.open_output(port_name)
        self._midi_out = midi_out
        midi_out.send(msg)

    #-----------------------------------------

    def open_input(self, port_num=0):
        """
        open midi input port
        from MidiManager object
        """

        input_names = mido.get_input_names()
        try:
            port_name = input_names[port_num]
            self._midi_in = mido.open_input(port_name)
            self._inport_num = port_num
            self._inport_name = port_name
        except IndexError:
            print(f"Error: opening midi input Port {port_num}")
        
        return self._midi_in

    #-----------------------------------------

    def open_output(self, port_num=0):
        """
        open midi output port
        from MidiManager object
        """

        output_names = mido.get_output_names()
        try:
            port_name = output_names[port_num]
            self._midi_out = mido.open_output(port_name)
            self._outport_num = port_num
            self._outport_name = port_name
        except IndexError:
            print(f"Error opening midi output Port {port_num}")
            self._midi_out = None
        
        return self._midi_out

    #-----------------------------------------

    def get_inport_id(self):
        """
        returns tuple with name and Midi Input port number 
        from MidiManager object
        """
        
        return (self._inport_num, self._inport_name)
    
    #-----------------------------------------
    
    def get_outport_id(self):
        """
        returns tuple with name and Midi Out port number 
        from MidiManager object
        """
        
        return (self._outport_num, self._outport_name)
    #-----------------------------------------

    def get_synth_type(self):
        """
        returns synth type
        from MidiManager object
        """
        
        return self._synth_type

    #-----------------------------------------

    def get_synth_id(self):
        """
        returns tuple with synth type, and Midi Out port number, and Audio Device
        from MidiManager object
        """
        
        return (self._synth_type, self._outport_num, self._audio_out)
    
    #-----------------------------------------

    def get_message_blocking(self, port=0):
        # Get incoming messages - blocking interface
        input_names = mido.get_input_names()
        port_name = input_names[port]
        in_port = mido.open_input(port_name)
        for msg in in_port: 
            print("\a") 
            print(msg)

    #-----------------------------------------

    def send_message(self, msg):
        """
        send incomming message to fluidsynth
        from MidiManager object
        """
        
        # print("Message in:", msg)
        type = msg.type
        bank =0
        if self._synth_type == 0:
            if self._midi_out:
                self._midi_out.send(msg)
        else:
            fs = self._synth_obj.fs
            if type in ['note_on', 'note_off']:
                chan = msg.channel
                
                note = msg.note
                msg.velocity =100
                vel = msg.velocity
                args = [chan, note, vel]
            if type == "note_on":
                fs.noteon(self.chan, msg.note, msg.velocity)
            elif type == "note_off":
                fs.noteoff(self.chan, msg.note)
            elif type == "program_change":
                fs.program_change(self.chan, msg.program)
            elif type == "control_change":
                fs.cc(self.chan, msg.control, msg.value)
            elif type == "pitchwheel":
                fs.pitch_bend(self.chan, msg.pitch)

        # notify toplevel application
        """
        if self.parent:
            self.parent.notify(msg)
        """

    #-----------------------------------------

    def output_message(self, msg):
        """
        output playback message to fluidsynth 
        distinguishing message channel
        from MidiManager object
        """
        
        # print("Message in:", msg)
        type = msg.type
        bank =0
        if self._synth_type == 0:
            if self._midi_out:
                self._midi_out.send(msg)
        else:
            fs = self._synth_obj.fs
            chan = msg.channel
            if type in ['note_on', 'note_off']:
                chan = msg.channel
                
                note = msg.note
                msg.velocity =100
                vel = msg.velocity
                args = [chan, note, vel]
            if type == "note_on":
                fs.noteon(chan, msg.note, msg.velocity)
            elif type == "note_off":
                fs.noteoff(chan, msg.note)
            elif type == "program_change":
                fs.program_change(chan, msg.program)
            elif type == "control_change":
                fs.cc(self.chan, msg.control, msg.value)
            elif type == "pitchwheel":
                fs.pitch_bend(self.chan, msg.pitch)

        # notify toplevel application
        """
        if self.parent:
            self.parent.notify(msg)
        """

    #-----------------------------------------

    def input_callback(self, msg):
        """
        incomming messages callback
        from MidiManager object
        """

        self.send_message(msg)

    #-----------------------------------------

    def receive_from(self, port_num=0, callback=None):
        """
        Get incoming messages - nonblocking interface
        with cb_func as callback
        """
        portname = ""

        inputnames = mido.get_input_names()
        try:
            port_name = inputnames[port_num]
            self._inport_num = port_num
            self._inport_name = port_name
        except IndexError:
            print(f"Error: Midi input Port {port_num} is not available")
        
        if port_name:
            midi_in = mido.open_input(port_name)
            self._midi_in = midi_in
            # or we can pass the callback function at the opening port:
            # in_port = mido.open_input(port_name, callback=cb_func)
            if callback:
                midi_in.callback = callback
        
    #-----------------------------------------

    def program_change(self, chan, program):
        """
        set program change
        from MidiManager object
        """
        
        if self._synth_type == 0 and self._midi_out:
            msg = mido.Message(type='program_change')
            msg.channel = chan
            msg.program = program
            self._midi_out.send(msg)
        elif self._synth_type == 1:
           if self._synth_obj.fs:
               self._synth_obj.fs.program_change(chan, program)
               # input callback function
        self.chan = chan

    #-----------------------------------------

    def bank_change(self, chan, bank):
        """
        change bank
        from MidiManager object
        """
        
        if self._synth_type == 0 and self._midi_out:
            msg = mido.Message(type='control_change')
            msg.channel = chan
            msg.value = bank
            self._midi_out.send(msg)
        elif self._synth_type ==1:
            if self._synth_obj.fs:
                self._synth_obj.fs.bank_select(chan, bank)

    #-----------------------------------------
        
    def panic(self, chan=-1):
        """
        set all notes off controller on al channels
        from MidiManager object
        """

        control = 123 # all notes off
        if self._synth_type == 0 and self._midi_out:
            msg = mido.Message(type='control_change')
            msg.channel =0
            msg.control = control
            msg.value =0
            if chan == -1: # all channels
                for chan in range(16):
                    msg.channel = chan
                    self._midi_out.send(msg)
            else:
                msg.channel = chan
                self._midi_out.send(msg)

        elif self._synth_type == 1: # synth_type = 0
            if self._synth_obj.fs:
                if chan == -1:
                    for chan in range(16):
                        self._synth_obj.fs.cc(chan, control, 0)
                else:
                    self._synth_obj.fs.cc(chan, control, 0)

    #-----------------------------------------

    def play_notes(self):
        """
        Test notes
        from MidiManager object
        """
        
        if self._synth_obj is None: 
            print("Error: Synth Engine is not available")
            return
        
        synth_obj = self._synth_obj
        synth_obj.program_change(0, 16)
        synth_obj.note_on(0, 60, 100)
        time.sleep(1.0)
        synth_obj.note_on(0, 67, 100)
        time.sleep(1.0)
        synth_obj.note_on(0, 76, 100)

        time.sleep(1.0)

        synth_obj.note_off(0, 60)
        synth_obj.note_off(0, 67)
        synth_obj.note_off(0, 76)

        time.sleep(1.0)

        """
        self._synth_obj.play_notes()
        if self._synth_type == 0:
            self.program_change(0, 16)
            self.note_on(0, 60, 100)
            time.sleep(1.0)
            self.note_off(0, 60)
            self.note_on(0, 67, 100)
            time.sleep(1.0)
            self.note_on(0, 76, 100)

            time.sleep(1.0)

            self.note_off(0, 60)
            self.note_off(0, 67)
            self.note_off(0, 76)
            time.sleep(1.0)


        elif self._synth_type == 1:
            if self._synth_obj: self._synth_obj.play_notes()
        """


    #-----------------------------------------

#========================================

if __name__ == "__main__":
    mid = MidiManager()
    mid.init_midi("")
    input("It's Ok")

