"""
This module contains the class for a pop up window to make a new or edit a profile.
version: 1.0.0 Initial commit by Roberts balulis
"""
__version__ = "1.0.0"

from tkinter import ttk
import ipaddress
import subprocess
import ctypes

import customtkinter

from create_log import setup_logger
from main_gui import App



class NetworkProfileToplevel(customtkinter.CTkToplevel):
    """Class for a pop up window to make a new or edit a profile.."""
    def __init__(self, app_instance:"App", network_data, *args, **kwargs):
        super().__init__( *args, **kwargs)

        self.app_instance = app_instance
        self.network_data = network_data
        self.logger = setup_logger(__name__)

        # Enable DPI awareness (checking scaling)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        # Window size
        width = 400
        height = 600

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position for centering
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

        self.title("Edit Profile" if self.network_data else "Create Profile")
        self.resizable(False, False)


        self.network_adapters = self.get_network_adapters()
        self.configure_ui()


    def configure_ui(self):
        """Configure the UI elements of the window."""
        label_font = customtkinter.CTkFont(size=16, weight="bold")
        entry_height = 35
        entry_width = 250

        if self.network_data:
            name_value, adapter_value, ip_value, subnet_value, gateway_value = self.network_data
        else:
            name_value, adapter_value, ip_value, subnet_value, gateway_value = "", self.network_adapters[0], "", "255.255.255.0", ""

        self.adapter_label = customtkinter.CTkLabel(self, text="Network Adapter", font=label_font)
        self.adapter_label.pack()
        self.adapter_combobox = customtkinter.CTkComboBox(self, values=self.network_adapters,
                                                          height=entry_height,
                                                          width=entry_width,
                                                          font=label_font)
        self.adapter_combobox.pack(pady=10)
        self.adapter_combobox.set(adapter_value if adapter_value in self.network_adapters else self.network_adapters[0])

        # Profile Name
        self.name_label = customtkinter.CTkLabel(self, text="Profile Name", font=label_font)
        self.name_label.pack()
        self.name_entry = customtkinter.CTkEntry(self, placeholder_text="Enter profile name",
                                                 height=entry_height,
                                                 width=entry_width,
                                                 font=label_font)
        self.name_entry.pack(pady=10)
        self.name_entry.insert(0, name_value)

        # IP Address
        self.ip_label = customtkinter.CTkLabel(self, text="IP Address", font=label_font)
        self.ip_label.pack()
        self.ip_entry = customtkinter.CTkEntry(self, placeholder_text="e.g. 192.168.1.10 or dhcp",
                                               height=entry_height,
                                               width=entry_width,
                                               font=label_font)
        self.ip_entry.pack(pady=10)
        if ip_value !="":
            self.ip_entry.insert(0, ip_value)
        self.ip_entry.bind("<FocusOut>", self.validate_ip)

        # Subnet Mask
        self.subnet_label = customtkinter.CTkLabel(self, text="Subnet Mask", font=label_font)
        self.subnet_label.pack()
        self.subnet_values = ["255.255.255.0", "255.255.0.0", "255.0.0.0", "Custom"]
        self.subnet_combobox = customtkinter.CTkComboBox(self, values=self.subnet_values,
                                                         command=self.handle_subnet_change,
                                                         height=entry_height,
                                                         width=entry_width,
                                                         font=label_font)
        self.subnet_combobox.pack(pady=10)

        # If the subnet is a common one, select it; otherwise, mark it as "Custom"
        if subnet_value in self.subnet_values:
            self.subnet_combobox.set(subnet_value)
            show_custom_subnet = False
        else:
            self.subnet_combobox.set("Custom")
            show_custom_subnet = True

        self.subnet_entry = customtkinter.CTkEntry(self, placeholder_text="Enter custom subnet",
                                                   height=entry_height,
                                                   width=entry_width,
                                                   font=label_font)
        self.subnet_entry.pack(pady=10)

        if show_custom_subnet:
            self.subnet_entry.insert(0, subnet_value)
        else:
            self.subnet_entry.pack_forget()

        # Gateway
        self.gateway_label = customtkinter.CTkLabel(self, text="Gateway", font=label_font)
        self.gateway_label.pack()
        self.gateway_entry = customtkinter.CTkEntry(self, placeholder_text="e.g. 192.168.1.1",
                                                    height=entry_height,
                                                    width=entry_width,
                                                    font=label_font)
        self.gateway_entry.pack(pady=10)
        self.gateway_entry.insert(0, gateway_value)
        self.gateway_entry.bind("<FocusOut>", self.validate_gateway)

        # Save Button
        self.save_button = customtkinter.CTkButton(self, text="Save", command=self.validate_and_save,
                                                   height=entry_height,
                                                   width=entry_width,
                                                   font=label_font)
        self.save_button.pack(pady=10)

        # Validation Message
        self.validation_label = customtkinter.CTkLabel(self, text="", text_color="red", font=label_font)
        self.validation_label.pack()

    def get_network_adapters(self):
        """Fetch available network adapters from the system."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-NetAdapter | Select-Object -ExpandProperty Name"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            adapters = [line.strip() for line in result.stdout.split("\n") if line.strip() and "NetConnectionID" not in line]
            return adapters if adapters else ["Ethernet"]
        except Exception as e:
            self.logger.error(f"Error: Failed to get network adapters: {e}")
            return ["Ethernet"]

    def handle_subnet_change(self, choice):
        """Handle dropdown selection for subnet."""
        if choice == "Custom":
            self.subnet_entry.pack()
        else:
            self.subnet_entry.pack_forget()


    def validate_ip(self, event=None):
        """Validate IP address format, allowing 'dhcp' as a valid input."""
        ip = self.ip_entry.get().strip().lower()

        if ip == "dhcp":
            self.ip_entry.configure(border_color="green", text_color="white")  # DHCP is valid
            return True

        try:
            ipaddress.IPv4Address(ip)
            self.ip_entry.configure(border_color="green", text_color="white")  # Valid static IP
            return True
        except ValueError:
            self.ip_entry.configure(border_color="red", text_color="red")  # Invalid input
            return False


    def validate_gateway(self, event=None):
        """Validate Gateway IP format and ensure it's in the same subnet, unless using DHCP."""
        ip = self.ip_entry.get().strip().lower()
        gateway = self.gateway_entry.get().strip()
        subnet = self.subnet_combobox.get() if self.subnet_combobox.get() != "Custom" else self.subnet_entry.get()

        # If DHCP is selected, skip validation and mark as valid
        if ip == "dhcp":
            self.gateway_entry.configure(border_color="green", text_color="white")
            return True

        try:
            ip_obj = ipaddress.IPv4Address(ip)
            gateway_obj = ipaddress.IPv4Address(gateway)
            network = ipaddress.IPv4Network(f"{ip}/{subnet}", strict=False)

            if gateway_obj in network:
                self.gateway_entry.configure(border_color="green", text_color="white")  # Valid
                return True
            else:
                self.gateway_entry.configure(border_color="red", text_color="red")  # Invalid
                return False
        except ValueError:
            self.gateway_entry.configure(border_color="red", text_color="red")  # Invalid
            return False



    def validate_and_save(self):
        """Final validation before saving."""
        if self.validate_ip() and self.validate_gateway():
            self.validation_label.configure(text="Settings saved successfully!", text_color="green")

            name = self.name_entry.get()
            self.logger.error(name)
            if name == "":
                return self.validation_label.configure(text="Invalid network settings!", text_color="red")

            adapter = self.adapter_combobox.get()
            ip = self.ip_entry.get()
            gateway = self.gateway_entry.get()
            subnet = self.subnet_combobox.get() if self.subnet_combobox.get() != "Custom" else self.subnet_entry.get()

            self.app_instance.add_profile(name=name, adapter=adapter, ip=ip, gateway=gateway, subnet=subnet)

        else:
            self.validation_label.configure(text="Invalid network settings!", text_color="red")
