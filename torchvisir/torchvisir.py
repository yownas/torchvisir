"""
torchvisir - your torch-installation guide
"""
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

class Torchvisir:
    """Functions to find a working versions for your GPU"""
    data = None
    pci_ids = None

    def _get_pci_ids_darwin(self):
        """Get GPUs on Apple computers"""
        try:
            res = subprocess.check_output([
                "system_profiler",
                "-json",
                "SPDisplaysDataType"
            ], text=True)
        except:
            res = ""
        ret = []
        try:
            data = json.loads(res)
            displays = data.get("SPDisplaysDataType", [])
            for display in displays:
                vendor_raw = display.get("spdisplays_vendor", "")
                device_id_raw = display.get("spdisplays_device-id", "")
                if device_id_raw and vendor_raw:
                    device_id = device_id_raw.replace("0x", "").lower()
                    if "Intel" in vendor_raw:
                        vendor_id = "8086"
                    else:
                        match = re.search(r"\((0x\w+)\)", vendor_raw)
                        if match:
                            vendor_id = match.group(1).replace("0x", "").lower()
                        else:
                            continue
                    ret.append(f"{str(vendor_id).lower()}:{str(device_id).lower()}")
        except:
            pass
        return ret

    def _get_pci_ids_linux(self):
        """Get GPUs on Linux"""
        try:
            res = subprocess.check_output([
                "lspci",
                "-nn"
            ], text=True)
        except Exception as e:
            print(f"ERROR: {e}")
            res = ""
        ret = []
        for line in res.splitlines():
            match = re.search(r"\[(\w+):(\w+)\]", line)
            if match:
                ret.append(f"{match.group(1).lower()}:{match.group(2).lower()}")
        return ret

    def _get_pci_ids_windows(self):
        """Get GPUs on Windows"""
        try:
            res = subprocess.check_output([
                "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "-Command",
                "Get-WmiObject Win32_VideoController | ForEach-Object { $_.PNPDeviceID }",
            ], text=True, stderr=subprocess.DEVNULL)
        except:
            res = ""
        ret = []
        for line in res.splitlines():
            match = re.search(r"VEN_(\w+)&DEV_(\w+)", line, re.IGNORECASE)
            if match:
                ret.append(f"{match.group(1).lower()}:{match.group(2).lower()}")
        return ret

    def get_pci_ids(self, tgt_os=None):
        """Get a list of all PCIe devices on the system"""
        self.pci_ids = []

        if tgt_os is None:
            tgt_os = platform.system()

        match tgt_os:
            case "Darwin":
                self.pci_ids = self._get_pci_ids_darwin()
            case "Linux":
                self.pci_ids = self._get_pci_ids_linux()
            case "Windows":
                self.pci_ids = self._get_pci_ids_windows()

        return self.pci_ids

    def clear_data(self):
        """Resets data."""
        self.data = None

    def load_data(self, folder=None):
        """Load json files in a folder to populate , may be run multiple times"""
        self.data = {}
        # Use a default path to GPU DB if it wasn't specified
        if folder is None:
            folder = Path(__file__).resolve().parent / 'tvdb'
        files = Path(folder).iterdir()
        for file in files:
            # Check if the file has a .json extension
            if str(file).endswith('.json'):
                #file_path = os.path.join(folder, file)
                file_path = file
                try:
                    # Import all JSON files into data
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        self.data.update(data)
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    def get_torch_targets(self, pci_ids=None):
        """Return a set of targets derived from your PCIe devices"""
        ret = set()
        if pci_ids is None:
            if self.pci_ids is None:
                self.get_pci_ids()
            pci_ids = self.pci_ids

        if self.data is None:
            self.load_data()

        if pci_ids is not None and self.data is not None:
            for device in pci_ids:
                if device in self.data['pci_id_data']:
                    ret.add(f"{self.data['pci_id_data'][device]}")
        return ret

    def install_torch(self, target=None, dry_run=False, force_reinstall=False):
        """Try to figure out a good pip-command for the current setup"""
        if target is None:
            target = self.get_torch_targets()

        if self.data is None:
            self.load_data()

        try:
            tgt = next(iter(target)) # TODO: We might have multiple targets
        except:
            # Fallback to 'cpu'
            tgt = 'cpu'

        tgt_sys = platform.system()
        tgt = f"{tgt}:{tgt_sys}"
        cmd = []
        for vendor in self.data['repos']:
            pattern = self.data['repos'][vendor]['pattern']
            if re.match(pattern, tgt):
                index_url = re.sub('TARGET', tgt, self.data['repos'][vendor]['index_url'])
                pkgs = []
                for pkg in self.data['repos'][vendor]['pkgs']:
                    pkgs.append(re.sub('TARGET', tgt, pkg))

                cmd = [sys.executable, '-m', 'pip', 'install']
                if force_reinstall:
                    cmd += ['--force-reinstall']
                cmd += pkgs
                if index_url:
                    cmd += ['--index-url', index_url]

                if not dry_run:
                    subprocess.check_output(cmd, text=True)
                break
        return ' '.join(cmd)
