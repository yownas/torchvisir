class torchvisir:
    tv_db = None
    pci_ids = None

    def get_pci_ids(self, sys=None):
        import json
        import platform
        import re
        import subprocess

        self.pci_ids = []

        if sys is None: sys = platform.system()

        match sys:
            case "Darwin":
                try:
                    res = subprocess.check_output([
                        "system_profiler",
                        "-json",
                        "SPDisplaysDataType"
                    ], text=True)
                except:
                    res = ""

                try:
                    data = json.loads(output)
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
                            self.pci_ids.append(f"{str(vendor_id).lower()}:{str(device_id).lower()}")
                except:
                    pass

            case "Linux":
                try:
                    res = subprocess.check_output([
                        "lspci",
                        "-nn"
                    ], text=True)
                except Exception as e:
                    res = ""

                for line in res.splitlines():
                    match = re.search(r"\[(\w+):(\w+)\]", line)
                    if match:
                        self.pci_ids.append(f"{match.group(1).lower()}:{match.group(2).lower()}")

            case "Windows":
                try:
                    res = subprocess.check_output([
                        "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                        "-Command",
                        "Get-WmiObject Win32_VideoController | ForEach-Object { $_.PNPDeviceID }",
                    ], text=True, stderr=subprocess.DEVNULL)
                except:
                    res = ""
                for line in res.splitlines():
                    match = re.search(r"VEN_(\w+)&DEV_(\w+)", line, re.IGNORECASE)
                    if match:
                        self.pci_ids.append(f"{match.group(1).lower()}:{match.group(2).lower()}")

        return self.pci_ids

    def clear_tv_db(self):
        self.tv_db = None

    def load_tv_db(self, folder=None):
        import json
        from pathlib import Path

        self.tv_db = {}
        if folder is None: folder = Path(__file__).resolve().parent / 'tvdb' # Default path to GPU DB
        files = Path.iterdir(folder)
        for file in files:
            # Check if the file has a .json extension
            if str(file).endswith('.json'):
                #file_path = os.path.join(folder, file)
                file_path = file
                try:
                    # Import all JSON files into tv_db
                    with open(file_path, 'r') as json_file:
                        data = json.load(json_file)
                        self.tv_db.update(data)
                except Exception as e:
                    print(f"Error reading {file}: {e}")
        return

    def get_torch_targets(self, pci_ids=None):
        ret = set()
        if pci_ids is None:
            if self.pci_ids is None:
                self.get_pci_ids()
            pci_ids = self.pci_ids

        if self.tv_db is None:
            self.load_tv_db()

        if pci_ids is not None and self.tv_db is not None:
            for device in pci_ids:
                if device in self.tv_db['pci_id_data']:
                    ret.add(f"{self.tv_db['pci_id_data'][device]}")
        return ret

    def install_torch(self, target=None, dry_run=False):
        import re
        import subprocess

        if target is None:
            target = self.get_torch_targets()
        
        tgt = next(iter(target)) # TODO: We might have multiple targets, but we'll only pick the first one
        for vendor in self.tv_db['repos']:
            if re.match(self.tv_db['repos'][vendor]['pattern'], tgt):
                index_url = re.sub('TARGET', tgt, self.tv_db['repos'][vendor]['index_url'])
                pkgs = []
                for pkg in self.tv_db['repos'][vendor]['pkgs']:
                    pkgs.append(re.sub('TARGET', tgt, pkg))
                cmd = ['pip', 'install'] + pkgs + ['--index-url', index_url]
                print("> ", cmd)
                if not dry_run:
                    subprocess.run(cmd)
                break



