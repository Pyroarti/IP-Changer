import sys
import subprocess
import customtkinter
from tkinter import ttk
import json
from pathlib import Path

from create_log import setup_logger

logger = setup_logger('main')

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("1000x650")
        self.title("IP Changer")
        self.resizable(False, False)

        self.json_path = Path("Data/profiles.json")

        self.setup_UI()

    def setup_UI(self):

        # Header
        header_button_height = 35
        header_button_width = 165
        header_button_font = customtkinter.CTkFont(size=16, weight="bold")

        self.header_frame = customtkinter.CTkFrame(master=self, height=50)
        self.header_frame.pack(side="top", fill="x", padx=5, pady=5)

        button_explore = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="New profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_explore.pack(side="left", padx=10, pady=5)

        button_delete = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="Delete selected profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_delete.pack(side="left", padx=5, pady=5)

        button_change_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="Edit selected profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_change_profile.pack(side="left", padx=5, pady=5)

        button_apply_profile = customtkinter.CTkButton(master=self.header_frame,
                                                 command=print("S"),
                                                 text="Apply selected profile",
                                                 width=header_button_width,
                                                 height=header_button_height,
                                                 font=header_button_font)
        button_apply_profile.pack(side="left", padx=5, pady=5)

        # Left frame
        self.left_frame = customtkinter.CTkFrame(master=self, width=290, height=350)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        left_label = customtkinter.CTkLabel(master=self.left_frame, text="Profiles",
                                            font=customtkinter.CTkFont(size=16, weight="bold"))
        left_label.pack(pady=10)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=30,
                        fieldbackground="#2b2b2b",
                        font=("Arial", 14))

        style.map("Treeview",
                  background=[("selected", "#1f6aa5")],
                  foreground=[("selected", "white")])

        style.configure("Treeview.Heading",
                        background="#1f1f1f",
                        foreground="white",
                        font=("Arial", 14, "bold"))

        # Treeview Widget
        self.tree = ttk.Treeview(self.left_frame, columns=("Profile", "Adapter", "IP", "Subnet", "Gateway"), show="headings")
        self.tree.heading("Profile", text="Profile")
        self.tree.heading("Adapter", text="Adapter")
        self.tree.heading("IP", text="IP Address")
        self.tree.heading("Subnet", text="Subnet Mask")
        self.tree.heading("Gateway", text="Gateway")

        self.tree.column("Profile", width=100, anchor="center")
        self.tree.column("Adapter", width=100, anchor="center")
        self.tree.column("IP", width=120, anchor="center")
        self.tree.column("Subnet", width=120, anchor="center")
        self.tree.column("Gateway", width=120, anchor="center")

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
                                           values=["Beijer", "Siemens"],
                                           command=print("S"))

        self.adapter_list.pack(pady=10)


    def load_data(self):
        if not self.json_path.exists():
            print(f" Error {self.json_path} ")
            default_data = {
                "1": {"Name": "Default", "Adapter":"Ethernet", "ip": "0.0.0.0", "subnet": "255.255.255.0", "gateway": "0.0.0.1"}
            }
            self.save_data(default_data)
            return default_data

        try:
            with self.json_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error")
            return {}


    def save_data(self, data):
        with self.json_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        print(f"Error")


    def populate_tree(self):
        """Fyller Treeview med nätverksdata"""
        # Rensa gamla data innan vi fyller på nytt
        for item in self.tree.get_children():
            self.tree.delete(item)

        for key, details in self.network_data.items():
            self.tree.insert("", "end", values=(
                details.get("Name", "N/A"),
                details.get("Adapter", "N/A"),
                details.get("ip", "N/A"),
                details.get("subnet", "N/A"),
                details.get("gateway", "N/A")
            ))

    def get_network_adapters(self):
        try:
            result = subprocess.run(["wmic", "nic", "get", "NetConnectionID"], capture_output=True, text=True)
            adapters = [line.strip() for line in result.stdout.split("\n") if line.strip() and "NetConnectionID" not in line]
            return adapters if adapters else ["Ethernet"]
        except Exception as e:
            print(self, "Error", f"Failed to get network adapters: {e}")
            return ["Ethernet"]


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
