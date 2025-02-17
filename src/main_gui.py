"""
Main gui for the IP-Changer
version: 1.0.0 Initial commit by Roberts balulis
"""

__version__ = "1.0.0"

import subprocess
from tkinter import ttk
import json
from pathlib import Path
import re
import ctypes

import customtkinter
from CTkMessagebox import CTkMessagebox

from create_log import setup_logger


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.logger = setup_logger(__name__)

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")

        # Enable DPI awareness (checking scaling)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        # Window size
        width = 1500
        height = 650

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position for centering
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

        self.title("IP Changer")
        self.resizable(False, False)

        self.json_path = Path("Data/profiles.json")
        self.network_adapters = self.get_network_adapters()

        self.profile_toplevel = None
        self.about_toplevel = None

        self.setup_UI()

    def setup_UI(self):

        # Header
        self.button_height = 35
        self.button_width = 165
        self.button_font = customtkinter.CTkFont(size=16, weight="bold")

        self.label_font = customtkinter.CTkFont(size=16, weight="bold")

        self.header_frame = customtkinter.CTkFrame(master=self, height=50)
        self.header_frame.pack(side="top", fill="x", padx=10, pady=5)

        button_new_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=self.open_profile_toplevel,
                                                 text="New profile",
                                                 width=self.button_width,
                                                 height=self.button_height,
                                                 font=self.button_font)
        button_new_profile.pack(side="left", padx=10, pady=5)

        button_delete = customtkinter.CTkButton(master=self.header_frame,
                                                 command=self.delete_profile,
                                                 text="Delete selected profile",
                                                 width=self.button_width,
                                                 height=self.button_height,
                                                 font=self.button_font)
        button_delete.pack(side="left", padx=10, pady=5)

        button_apply_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="Apply selected profile",
                                                 width=self.button_width,
                                                 height=self.button_height,
                                                 font=self.button_font)
        button_apply_profile.pack(side="left", padx=10, pady=5)

        button_about = customtkinter.CTkButton(master=self.header_frame,
                                         command=self.open_about_toplevel,
                                         text="About",
                                         width=self.button_width,
                                         height=self.button_height,
                                         font=self.button_font)
        button_about.pack(side="right", padx=10, pady=5)

        # Left frame
        self.left_frame = customtkinter.CTkFrame(master=self, width=290, height=350)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        left_label = customtkinter.CTkLabel(master=self.left_frame, text="Profiles",
                                            font=self.label_font)
        left_label.pack(pady=10)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=35,
                        fieldbackground="#2b2b2b",
                        font=("Arial", 14),
                        borderwidth=0)

        style.map("Treeview",
                  background=[("selected", "#1f6aa5")],
                  foreground=[("selected", "white")])

        style.configure("Treeview.Heading",
                        background="#1f1f1f",
                        foreground="white",
                        font=("Arial", 14, "bold"),
                        relief="flat")

        style.map("Treeview.Heading",
                  background=[("active", "#2f2f2f")])

        self.tree = ttk.Treeview(self.left_frame, columns=("Profile", "Adapter", "IP", "Subnet", "Gateway"), show="headings", selectmode="browse")
        self.tree.bind("<Double-1>", self.OnDoubleClick)

        columns = [("Profile", 180), ("Adapter", 180), ("IP", 130), ("Subnet", 130), ("Gateway", 130)]
        for col, width in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=width, anchor="center")

        #TODO Make this nicer
        #tree_scroll = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.tree.yview)
        #self.tree.configure(yscrollcommand=tree_scroll.set)

        #tree_scroll.pack(side="right", fill="y")

        self.tree.pack(expand=True, fill="both", padx=5, pady=5)

        self.network_data = self.load_data()
        self.populate_tree()

        # Right frame
        self.right_frame = customtkinter.CTkFrame(master=self, width=290, height=350)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.scrollable_right_frame = customtkinter.CTkScrollableFrame(master=self.right_frame, width=290, height=320)
        self.scrollable_right_frame.pack(fill="both", expand=True, padx=5, pady=5)

        right_label = customtkinter.CTkLabel(master=self.scrollable_right_frame, text="Current Network Status",
                                             font=customtkinter.CTkFont(size=16, weight="bold"))
        right_label.pack(pady=10)

        self.adapter_labels = {}

        self.update_button = customtkinter.CTkButton(master=self.right_frame, text="Refresh list", command=self.refresh_adapters,
                                                     width=self.button_width,
                                                    height=self.button_height,
                                                    font=self.button_font)
        self.update_button.pack(pady=10)

        self.refresh_adapters()


    def refresh_adapters(self):
        """Fetch the latest adapter info and update the UI."""
        self.adapter_labels.clear()

        for widget in self.scrollable_right_frame.winfo_children():
            widget.destroy()

        right_label = customtkinter.CTkLabel(master=self.scrollable_right_frame, text="Current Network Status",
                                             font=customtkinter.CTkFont(size=16, weight="bold"))
        right_label.pack(pady=10)

        adapters = self.get_network_adapters()
        for adapter in adapters:
            ip, subnet, gateway = self.get_network_info(adapter)

            adapter_title = customtkinter.CTkLabel(self.scrollable_right_frame, text=f"{adapter}", font=self.label_font)
            adapter_title.pack(pady=5)

            ip_label = customtkinter.CTkLabel(self.scrollable_right_frame, text=f"IP: {ip}", font=self.label_font)
            ip_label.pack()

            subnet_label = customtkinter.CTkLabel(self.scrollable_right_frame, text=f"Subnet: {subnet}", font=self.label_font)
            subnet_label.pack()

            gateway_label = customtkinter.CTkLabel(self.scrollable_right_frame, text=f"Gateway: {gateway}", font=self.label_font)
            gateway_label.pack(pady=5)

            separator = customtkinter.CTkLabel(self.scrollable_right_frame, text="----------------------------", font=self.label_font)
            separator.pack(pady=5)

            self.adapter_labels[adapter] = (ip_label, subnet_label, gateway_label)


    def OnDoubleClick(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            data = self.tree.item(selected_item[0], "values")
            self.open_profile_toplevel(data)


    def load_data(self):
        """Loads network data from JSON file or creates default data if the file doesn't exist."""
        if not self.json_path.exists():
            print(f"File not found: {self.json_path}, creating default data.")
            default_data = {
                "profiles": [
                    {
                        "name": "Default",
                        "adapter": "Ethernet",
                        "ip": "0.0.0.0",
                        "subnet": "255.255.255.0",
                        "gateway": "0.0.0.1"
                    }
                ]
            }
            self.save_data(default_data)
            return default_data

        try:
            with self.json_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error: JSON Decode Failed.")
            return {"profiles": []}


    def save_data(self, data):
        """Saves network data to JSON file."""
        try:
            with self.json_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")


    def delete_profile(self):
        """Deletes the selected profile from the JSON file and updates the tree view."""
        msg = CTkMessagebox(title="Delete?", message="Are you sure you want to delete the profile?",
                        icon="question", option_1="No", option_2="Yes", font=self.label_font)
        response = msg.get()

        if response=="No":
            return

        selected_item = self.tree.selection()
        if not selected_item:
            print("No profile selected.")
            return

        profile_values = self.tree.item(selected_item, "values")
        if not profile_values:
            print("Failed to get profile values.")
            return

        profile_name = profile_values[0]


        self.network_data["profiles"] = [p for p in self.network_data["profiles"] if p["name"] != profile_name]

        self.save_data(self.network_data)

        self.populate_tree()



    def add_profile(self, name, adapter, ip, subnet, gateway):
        """Adds a new network profile."""
        new_profile = {
            "name": name,
            "adapter": adapter,
            "ip": ip,
            "subnet": subnet,
            "gateway": gateway
        }

        self.network_data["profiles"].append(new_profile)
        self.save_data(self.network_data)

        self.populate_tree()


    def open_profile_toplevel(self, data=None):
        """Opens a popup to maake a new profile or edit one"""

        from profile_toplevel import NetworkProfileToplevel

        if not hasattr(self, 'profile_toplevel') or self.profile_toplevel is None or not self.profile_toplevel.winfo_exists():
            self.profile_toplevel = NetworkProfileToplevel(self, data)
            self.profile_toplevel.focus()
            self.profile_toplevel.attributes('-topmost', True)

        if hasattr(self, 'profile_toplevel') and self.profile_toplevel.winfo_exists():
            self.profile_toplevel.focus()
            self.profile_toplevel.lift()


    def open_about_toplevel(self):
        """Opens a popup to maake a new profile or edit one"""

        from about_toplevel import AboutToplevel

        if not hasattr(self, 'about_toplevel') or self.about_toplevel is None or not self.about_toplevel.winfo_exists():
            self.about_toplevel = AboutToplevel(self)
            self.about_toplevel.focus()
            self.about_toplevel.attributes('-topmost', True)

        if hasattr(self, 'about_toplevel') and self.about_toplevel.winfo_exists():
            self.about_toplevel.focus()
            self.about_toplevel.lift()


    def populate_tree(self):
        """Fills Treeview with network data."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for profile in self.network_data.get("profiles", []):
            self.tree.insert("", "end", values=(
                profile.get("name", "N/A"),
                profile.get("adapter", "N/A"),
                profile.get("ip", "N/A"),
                profile.get("subnet", "N/A"),
                profile.get("gateway", "N/A")
            ))

    def get_network_adapters(self):
        try:
            result = subprocess.run(
            [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", "-Command", "Get-NetAdapter | Select-Object -ExpandProperty Name"],
            capture_output=True,
            text=True
            )

            adapters = [line.strip() for line in result.stdout.split("\n") if line.strip()]

            return adapters if adapters else ["Ethernet"]

        except Exception as e:
            print(self, "Error:", f"Failed to get network adapters: {e}")
            return ["Ethernet"]


    def get_network_info(self, adapter):
        """Fetch IP Address, Subnet Mask, and Default Gateway for the given adapter"""
        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            output = result.stdout

            # Use regex to find the relevant adapter section
            adapter_section = re.search(rf"{adapter}.*?:\s+(.+?)\n\n", output, re.DOTALL)
            if not adapter_section:
                return "N/A", "N/A", "N/A"

            adapter_data = adapter_section.group(1)

            # Extract IP Address
            ip_match = re.search(r"IPv4 Address[.\s]+: ([\d.]+)", adapter_data)
            ip = ip_match.group(1) if ip_match else "N/A"

            # Extract Subnet Mask
            subnet_match = re.search(r"Subnet Mask[.\s]+: ([\d.]+)", adapter_data)
            subnet = subnet_match.group(1) if subnet_match else "N/A"

            # Extract Default Gateway
            gateway_match = re.search(r"Default Gateway[.\s]+: ([\d.]+)", adapter_data)
            gateway = gateway_match.group(1) if gateway_match else "N/A"

            return ip, subnet, gateway

        except Exception as e:
            print(f"Error retrieving network info: {e}")
            return "N/A", "N/A", "N/A"


    def apply_settings(self):
        adapter = self.adapter_combo.currentText()
        profile_name = self.profile_combo.currentText()
        if profile_name == "DHCP":
            self.set_dhcp(adapter)
        else:
            self.set_static_ip(adapter, self.profiles[profile_name])


    def set_dhcp(self, adapter):
        try:
            subprocess.run(["netsh", "interface", "ip", "set", "address", f"name={adapter}", "source=dhcp"], check=True)
            subprocess.run(["netsh", "interface", "ip", "set", "dns", f"name={adapter}", "source=dhcp"], check=True)
            print(self, "Success", "DHCP enabled successfully.")
        except subprocess.CalledProcessError as e:
            print(self, "Error", f"Failed to enable DHCP: {e}")


    def set_static_ip(self, adapter, profile):
        try:
            subprocess.run(["netsh", "interface", "ip", "set", "address", f"name={adapter}", "static",
                            profile["ip"], profile["subnet"], profile["gateway"]], check=True)
            print(self, "Success", "Static IP applied successfully.")
        except subprocess.CalledProcessError as e:
            print(self, "Error", f"Failed to apply static IP: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
