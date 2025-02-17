"""
This module contains the class for the about pop up window
version: 1.0.0 Initial commit by Roberts balulis
"""
__version__ = "1.0.0"

import ctypes
import tkinter as tk
from pathlib import Path

import customtkinter
from PIL import Image, ImageTk

from create_log import setup_logger
from main_gui import App

# Just for jokes
TEXT = "This software is made and owned by Roberts Balulis. Any unauthorized copying will delete your system32. This was made in my free time and not on work. Here is proof"


class AboutToplevel(customtkinter.CTkToplevel):
    """Class for a pop up window to make a new or edit a profile.."""
    def __init__(self, app_instance:"App", *args, **kwargs):
        super().__init__( *args, **kwargs)

        self.app_instance = app_instance
        self.logger = setup_logger(__name__)

        # Enable DPI awareness (checking scaling)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        # Window size
        width = 800
        height = 450

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position for centering
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

        self.title("Profile")
        self.resizable(False, False)

        self.configure_ui()


    def configure_ui(self):
        """Configure the UI elements of the window."""
        label_font = customtkinter.CTkFont(size=18, weight="bold")

        self.about_text = customtkinter.CTkLabel(self, text=TEXT, font=label_font, wraplength=700)
        self.about_text.pack(pady=10)

        image = Image.open("assets/About_pic.jpg")
        rotated_image = image.rotate(90, expand=True)

        self.bg_image = ImageTk.PhotoImage(rotated_image.resize((800, 400)))

        bg_image_label = customtkinter.CTkLabel(self, image=self.bg_image, text="")
        bg_image_label.pack(pady=10)


