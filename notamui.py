    # This file is part of NotamPlotter.
    
    # NotamPlotter plots notams on a streetmap.
    # Copyright (C) 2023  Jelmer Korten (korty.codes)

    # NotamPlotter is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # NotamPlotter is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with NotamPlotter.  If not, see <https://www.gnu.org/licenses/>.

    # Contact: korty.codes@gmail.com

# Notam gui
# TODO: rewrite getnotams to fetch notams again if file already exists


# Notam gui

import customtkinter as ctk
import tkinter as tk

import notam_util as nu
import os
from datetime import date


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup window.
        self.title("Notam Plot")
        self.WIDTH = 310
        self.HEIGHT = 150
        self.SWIDTH = self.winfo_screenwidth()
        self.SHEIGHT = self.winfo_screenheight()
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{int((self.SWIDTH/2)-(self.WIDTH/2))}+{int((self.SHEIGHT/2)-(self.HEIGHT/2))}")
        self.popup = None
        self.overwrite = False
        self.airports = "omae omaa omad"
        self.airport_str = "_".join(self.airports.split(" "))
        self.current_frame = None

        # Create initial frame
        self.frame1 = ctk.CTkFrame(self)
        self.frame1.pack()
        self.current_frame = self.frame1

        # Create popup frame
        self.frame2 = ctk.CTkFrame(self)
        
        # Create collect done frame
        self.frame3 = ctk.CTkFrame(self)

        # Create plot output frame
        self.frame4 = ctk.CTkFrame(self)

        # Create an entry box for frame1
        self.entrytext = tk.StringVar(value="omae omaa omad")
        self.entry = ctk.CTkEntry(self.frame1, textvariable= self.entrytext, width=200)
        self.entry.grid(row=0,column=0,columnspan=4, padx=(10,10), pady=(10,10), sticky="nsew")
        
        # Create 2 buttons for frame1
        self.collect_button = ctk.CTkButton(self.frame1, text = "Collect Notams", command = lambda: self.collect_frame1())
        self.collect_button.grid(row=1,column=1,columnspan=1, padx=(10,5), pady=(10,10), sticky="nsew")
        self.plot_button = ctk.CTkButton(self.frame1, text = "Create Plot File", command = self.plot_func)
        self.plot_button.grid(row=1,column=3,columnspan=1, padx=(5,10), pady=(10,10), sticky="nsew")

        # Create 2 buttons for frame2
        self.label = ctk.CTkLabel(self.frame2, text="File already exists\n\nOverwrite Current file and\nget new notams or\nUse Existing")
        self.label.grid(row=0,column=0,columnspan=2, padx=(10,10), pady=(10,10), sticky="nsew")
        self.get_anyway = ctk.CTkButton(self.frame2, text="Overwrite Current", command= lambda: self.collect_frame2())
        self.get_anyway.grid(row=1,column=0,columnspan=1, padx=(10,5), pady=(10,10), sticky="nsew")
        self.plot_current = ctk.CTkButton(self.frame2, text="Use Existing", command=self.plot_func)
        self.plot_current.grid(row=1,column=1,columnspan=1, padx=(5,10), pady=(10,10), sticky="nsew")

        # Create frame3 message
        self.frame3_label = ctk.CTkLabel(self.frame3, text="Collecting of data done")
        self.frame3_button = ctk.CTkButton(self.frame3, text="Ok", command=self.frame3button)
        self.frame3_label.pack()
        self.frame3_button.pack()

        # Create frame4 message
        self.frame4_label = ctk.CTkLabel(self.frame4, text="Plot file created.\nYou can find it in the output folder")
        self.frame4_button = ctk.CTkButton(self.frame4, text="Ok", command=self.frame4button)
        self.frame4_label.pack()
        self.frame4_button.pack()

    def frame4button(self):
        self.current_frame.pack_forget()
        self.frame1.pack()
        self.current_frame = self.frame1

    def frame3button(self):
        self.current_frame.pack_forget()
        self.frame1.pack()
        self.current_frame = self.frame1


    def collect_frame2(self):
        nu.collect(self.airports)
        self.current_frame.pack_forget()
        self.frame3.pack()
        self.current_frame = self.frame3


    def collect_frame1(self):
        today = date.today().strftime("%Y%m%d")
        url = f"files/{today}_notams_{'_'.join(self.airports.split(' '))}.csv"
        self.airports = self.entry.get()
        self.airport_str = '_'.join(self.airports.split(' '))
        if os.path.isfile(url):
            self.current_frame.pack_forget()
            self.frame2.pack()
            self.current_frame = self.frame2


    def plot_func(self):
        today = date.today().strftime("%Y%m%d")
        url = f"files/{today}_notams_{self.airport_str}.csv"
        if os.path.isfile(url):
            nu.handle(airports_str=self.airport_str)
            self.current_frame.pack_forget()
            self.frame4.pack()
            self.current_frame = self.frame4
        else:
            nu.collect(self.airports)
            nu.handle(airports_str=self.airport_str)
            self.current_frame.pack_forget()
            self.frame4.pack()
            self.current_frame = self.frame4


if __name__ == "__main__":
    app = App()
    app.mainloop()