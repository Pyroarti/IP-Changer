import subprocess

def get_network_adapters():
    try:
        # Hämta alla nätverksadaptrar
        result = subprocess.run(
            ["powershell", "-Command", "Get-NetAdapter | Select-Object -ExpandProperty Name"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(result)

        adapters = [line.strip() for line in result.stdout.split("\n") if line.strip()]

        # Om inga adaptrar hittas, returnera en default
        if not adapters:
            adapters = ["Ethernet"]

        adapter_info = {}
        for adapter in adapters:
            # Hämta DHCP-status genom att kolla om en DHCP-server är tilldelad
            dhcp_result = subprocess.run(
                ["powershell", "-Command", f"Get-NetIPConfiguration -InterfaceAlias '{adapter}' | Select-Object -ExpandProperty IPv4Interface | Select-Object -ExpandProperty Dhcp"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            dhcp_status = dhcp_result.stdout.strip()

            adapter_info[adapter] = "DHCP" if "Enabled" in dhcp_status else "Static"

        return adapter_info

    except Exception as e:
        print(f"Error: Failed to get network adapters: {e}")
        return {"Ethernet": "Unknown"}

# Testa funktionen
if __name__ == "__main__":
    adapters = get_network_adapters()
    for adapter, dhcp_status in adapters.items():
        print(f"Adapter: {adapter}, DHCP: {dhcp_status}")
