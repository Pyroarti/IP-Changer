import sys
import subprocess
import customtkinter
from tkinter import ttk
import json
from pathlib import Path
import re

from create_log import setup_logger



logger = setup_logger('main')

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("1500x650")
        self.title("IP Changer")
        self.resizable(False, False)

        self.json_path = Path("Data/profiles.json")
        self.network_adapters = self.get_network_adapters()

        self.profile_toplevel = None

        self.setup_UI()

    def setup_UI(self):

        # Header
        header_button_height = 35
        header_button_width = 165
        header_button_font = customtkinter.CTkFont(size=16, weight="bold")

        label_font = customtkinter.CTkFont(size=16, weight="bold")

        self.header_frame = customtkinter.CTkFrame(master=self, height=50)
        self.header_frame.pack(side="top", fill="x", padx=10, pady=5)

        button_new_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=self.open_profile_toplevel,
                                                 text="New profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_new_profile.pack(side="left", padx=10, pady=5)

        button_delete = customtkinter.CTkButton(master=self.header_frame,
                                                 command=self.delete_profile,
                                                 text="Delete selected profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_delete.pack(side="left", padx=10, pady=5)

        button_change_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="Edit selected profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_change_profile.pack(side="left", padx=10, pady=5)

        button_apply_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="Apply selected profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_apply_profile.pack(side="left", padx=10, pady=5)

        # Left frame
        self.left_frame = customtkinter.CTkFrame(master=self, width=290, height=350)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        left_label = customtkinter.CTkLabel(master=self.left_frame, text="Profiles",
                                            font=label_font)
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

        self.tree = ttk.Treeview(self.left_frame, columns=("Profile", "Adapter", "IP", "Subnet", "Gateway"), show="headings")

        columns = [("Profile", 180), ("Adapter", 180), ("IP", 130), ("Subnet", 130), ("Gateway", 130)]
        for col, width in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=width, anchor="center")

        #tree_scroll = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.tree.yview)
        #self.tree.configure(yscrollcommand=tree_scroll.set)

        #tree_scroll.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both", padx=5, pady=5)

        self.network_data = self.load_data()
        self.populate_tree()

        # Right frame
        self.right_frame = customtkinter.CTkFrame(master=self, width=290, height=350)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        right_label = customtkinter.CTkLabel(master=self.right_frame, text="Current status",
                                             font=customtkinter.CTkFont(size=16, weight="bold"))
        right_label.pack(pady=10)

        self.adapter_list = customtkinter.CTkComboBox(master=self.right_frame,
                                          values=self.network_adapters,
                                          width=250,
                                          height=35,
                                          command=self.update_adapter_info)

        self.adapter_list.pack(pady=10)

        self.ip_label = customtkinter.CTkLabel(self.right_frame, text="", font=label_font)
        self.ip_label.pack(pady=10)

        self.subnet_label = customtkinter.CTkLabel(self.right_frame, text="", font=label_font)
        self.subnet_label.pack(pady=10)

        self.gateway_label = customtkinter.CTkLabel(self.right_frame, text="", font=label_font)
        self.gateway_label.pack(pady=10)


    def update_adapter_info(self, adapter):
        """Update the labels with current network details of the selected adapter."""
        ip, subnet, gateway = self.get_network_info(adapter)

        # Update labels
        self.ip_label.configure(text=f"IP Address: {ip}")
        self.subnet_label.configure(text=f"Subnet Mask: {subnet}")
        self.gateway_label.configure(text=f"Gateway: {gateway}")



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
        selected_item = self.tree.selection()  # Get selected row
        if not selected_item:
            print("No profile selected.")
            return

        profile_values = self.tree.item(selected_item, "values")
        if not profile_values:
            print("Failed to get profile values.")
            return

        profile_name = profile_values[0]  # The first column contains the profile name

        # Remove the profile from network_data
        self.network_data["profiles"] = [p for p in self.network_data["profiles"] if p["name"] != profile_name]

        # Save the updated data
        self.save_data(self.network_data)

        # Refresh the tree view
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
        # Refresh the tree view
        self.populate_tree()

    def open_profile_toplevel(self):
        """Opens a popup to maake a new profile or edit one"""

        from profile_toplevel import NetworkProfile

        if not hasattr(self, 'profile_toplevel') or self.profile_toplevel is None or not self.profile_toplevel.winfo_exists():
            self.profile_toplevel = NetworkProfile(self)
            self.profile_toplevel.focus()
            self.profile_toplevel.attributes('-topmost', True)

        if hasattr(self, 'profile_toplevel') and self.profile_toplevel.winfo_exists():
            self.profile_toplevel.focus()
            self.profile_toplevel.lift()


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
            result = subprocess.run(["wmic", "nic", "get", "NetConnectionID"], capture_output=True, text=True)
            adapters = [line.strip() for line in result.stdout.split("\n") if line.strip() and "NetConnectionID" not in line]
            return adapters if adapters else ["Ethernet"]
        except Exception as e:
            print(self, "Error", f"Failed to get network adapters: {e}")
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
