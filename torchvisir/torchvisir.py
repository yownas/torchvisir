"""
torchvisir - your torch-installation guide
"""
import json
import logging
import platform
import re
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_DB = Path(__file__).resolve().parent / "tvdb"

def _deep_merge(base: dict, new: dict) -> dict:
    """Recursively merge `new` into `base` (in place). Later values win;
    nested dicts are merged, anything else (including lists) is replaced."""
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base

class Torchvisir:
    """Functions to find a working versions for your GPU"""
    def __init__(self):
        self.data = {}
        self.pci_ids = []

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
            log.error("Error running lspci: %s", e)
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
        self.data = {}

    def load_data(self, folder=None):
        """Load json files in a folder to populate , may be run multiple times"""
        # Use a default path to GPU DB if it wasn't specified
        folder = Path(folder) if folder is not None else DEFAULT_DB
        if not folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {folder}")

        for file in sorted(folder.glob("*.json")):
            try:
                with open(file, "r", encoding="utf-8") as fh:
                    content = json.load(fh)
            except (OSError, json.JSONDecodeError) as e:
                log.warning("Skipping %s: %s", file, e)
                continue
            if not isinstance(content, dict):
                log.warning("Skipping %s: top level must be a JSON object", file)
                continue
            _deep_merge(self.data, content)

    def get_torch_targets(self, pci_ids=None):
        """Return a set of targets derived from your PCIe devices"""
        ret = set()
        if pci_ids is None:
            if len(self.pci_ids) == 0:
                self.get_pci_ids()
            pci_ids = self.pci_ids

        if len(self.data) == 0:
            self.load_data()

        if len(pci_ids) > 0 and len(self.data) > 0:
            for device in pci_ids:
                if device in self.data['pci_id_data']:
                    ret.add(f"{self.data['pci_id_data'][device]}")
        return ret

    def install_torch(self, target=None, dry_run=False, force_reinstall=False):
        """Try to figure out a good pip-command for the current setup"""
        if target is None:
            target = self.get_torch_targets()

        if len(self.data) == 0:
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
