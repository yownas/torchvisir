'''
Update tvdb/gpus.json before release
'''
# Converts the txt file at https://github.com/pciutils/pciids/blob/master/pci.ids to json

import argparse
import json
import re
import sys

GPU_VENDOR_MAPPINGS = {
    # AMD
    #   https://github.com/ROCm/TheRock/blob/main/RELEASES.md#gfx-target-lookup-table
    "1002": {
        "AMD Instinct MI355X / MI350X:gfx950": re.compile(r"\[Instinct (MI355X|MI350X)\]", re.IGNORECASE),
        "AMD Instinct MI325X / MI300X / MI300A:gfx942": re.compile(r"\[Instinct (MI325X|MI300X|MI300A)", re.IGNORECASE),
        "AMD Instinct MI250X / MI250 / MI210:gfx90a": re.compile(r"\[Instinct (MI250X|MI250X/MI250|MI210)", re.IGNORECASE),
        "AMD Instinct MI100:gfx908": re.compile(r"\[Instinct (MI100)", re.IGNORECASE),
        "AMD Instinct MI60 / MI50, Radeon Pro VII, Radeon VII:gfx906": re.compile(r"Vega 20", re.IGNORECASE),
        "AMD Instinct MI25:gfx900": re.compile(r"Vega 20", re.IGNORECASE),
        "AMD Radeon RX 9070 / XT, AI PRO R9700 / R9600D:gfx1201": re.compile(r"Navi 48 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 9060 / XT:gfx1200": re.compile(r"Navi 44 \[Radeon", re.IGNORECASE),
        "AMD Radeon 820M iGPU:gfx1153": re.compile(r"Krackan2 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 7600:gfx1102": re.compile(r"Navi 33 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 7800 XT / 7700 XT, PRO V710 / W7700:gfx1101": re.compile(r"Navi 32 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 7900 XTX / 7900 XT, PRO W7900 / W7800:gfx1100": re.compile(r"Navi 31 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 6900 XT / 6800 XT, PRO W6800 / V620:gfx1030": re.compile(r"Navi 21 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 6750 XT / 6700 XT:gfx1031": re.compile(r"Navi 22 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 6600 XT / 6600, PRO W6600:gfx1032": re.compile(r"Navi 23 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 6500 XT:gfx1034": re.compile(r"Navi 24 \[Radeon", re.IGNORECASE),
        "AMD Radeon RX 5700 / XT:gfx1010": re.compile(r"Navi 10 \[Radeon", re.IGNORECASE),
        "AMD Radeon Pro V520:gfx1011": re.compile(r"Navi 12 \[Radeon", re.IGNORECASE),
        "AMD Radeon Pro W5500:gfx1012": re.compile(r"Navi 14 \[Radeon", re.IGNORECASE),
    },
    # Supported by TheRock but not found (?) in PCIid db.
    # AMD Ryzen AI 7 350 gfx1152
    # AMD Ryzen AI Max+ PRO 395 gfx1151
    # AMD Ryzen AI 9 HX 375	gfx1150	device-gfx1150
    # AMD Ryzen 7 7840U / Ryzen 9 270	gfx1103	device-gfx1103
    # AMD Van Gogh iGPU	gfx1033	device-gfx1033
    # AMD Radeon 680M iGPU	gfx1035	device-gfx1035
    # AMD Raphael iGPU	gfx1036	device-gfx1036

    # INTEL
    #   https://download.pytorch.org/whl/xpu
    "8086": {
       "Intel XPU:xpu": re.compile(r"DG2 ", re.IGNORECASE),
    },

    # NVIDIA
    #   https://github.com/easydiffusion/torchruntime/blob/main/torchruntime/gpu_db.py
    #   https://en.wikipedia.org/wiki/CUDA
    #   https://download.pytorch.org/whl/
    "10de": {
        # Kepler - sm3.7 - Too old, sorry.
        "Maxwell:cu126": re.compile(r"\b(gm\d+\w*)\b", re.IGNORECASE), # Maxwell - sm5
        "Pascal:cu126": re.compile(r"\b(gp\d+\w*)\b", re.IGNORECASE), # Pascal - sm6
        "Volta:cu126": re.compile(r"\b(gv\d+\w*)\b", re.IGNORECASE),  # Volta - sm7
        "Turing:cu130": re.compile(r"\b(tu\d+\w*)\b", re.IGNORECASE), # Turing - sm7.5
        "Ampere:cu130": re.compile(r"\b(ga\d+\w*)\b", re.IGNORECASE), # Ampere - sm8.6
        "AdaLovelace:cu130": re.compile(r"\b(ad\d+\w*)\b", re.IGNORECASE), # Ada Lovelace - sm8.9
        "GraceHopper:cu130": re.compile(r"\b(gh\d+\w*)\b", re.IGNORECASE), # Grace Hopper - sm9.0
        "Blackwell:cu130": re.compile(r"\b(?:gb\d+\w*|5060|5070|5080|5090)\b", re.IGNORECASE), # Blackwell - sm10, sm12
    },
}

######################################

SKIP_LINE_REGEX = re.compile(r"^\t{2,}")
VENDOR_REGEX = re.compile(r"^([0-9a-f]{4})\s+(.*)", re.IGNORECASE)
DEVICE_REGEX = re.compile(r"^\t([0-9a-f]{4})\s+(.*)", re.IGNORECASE)

SUBDEVICE_REGEX = re.compile(r"^\t\t([0-9a-f]{4})\s+([0-9a-f]{4})\s+(.*)", re.IGNORECASE)

# Pre-filled with some cards (non-main-vendor && non-subdevices)
pci_id_data = {
    "pci_id_data": {
        "1458:1002": "gfx1030", # Gigabyte Technology Co., Ltd : Aourus Radeon rx6900XT Xtreme Waterforce WB 16G
        "1458:2425": "gfx1202", # Gigabyte Technology Co., Ltd : Radeon RX 9070 GAMING OC 16G
    }
}

def process_pci_file(args):
    '''
    Parse the pci_id file and find GPUs that match the vendor patterns above
    '''
    vendor_id, _ = None, None

    input_file=args.filename

    with open(input_file, "r", encoding="utf-8") as file:
        add_subdevices = False
        for line in file:
            # Skip comments and deeply indented lines (2 or more indents)
            #if line.startswith("#") or SKIP_LINE_REGEX.match(line):
            if line.startswith("#"):
                continue

            # Match vendor lines (no tab)
            match_vendor = VENDOR_REGEX.match(line)
            if match_vendor:
                vendor_id, _ = match_vendor.groups()
                continue  # Move to next line for processing

            if vendor_id not in GPU_VENDOR_MAPPINGS:
                continue # Skip all non-gpu-vendor lines

            # Match subdevice lines (two tabs)
            if add_subdevices:
                match_subdevice = SUBDEVICE_REGEX.match(line)
                if match_subdevice:
                    tmp_vendor_id, device_id, device_name = match_subdevice.groups()
                    if args.lookup is None:
                        pci_id_data["pci_id_data"][f"{tmp_vendor_id}:{device_id}"] = gpu_arch
                    elif args.lookup == f"{tmp_vendor_id}:{device_id}":
                        print(f"{tmp_vendor_id}:{device_id}    {device_name}")
                else:
                    add_subdevices = False # Not a subdevice line, stop looking

            # Match device lines (single tab)
            match_device = DEVICE_REGEX.match(line)
            if match_device:
                device_id, device_name = match_device.groups()

                # Insert the vendor and device information in dict
                for gpu in GPU_VENDOR_MAPPINGS[vendor_id]:
                    pat = GPU_VENDOR_MAPPINGS[vendor_id][gpu]
                    if pat.search(device_name):
                        _ , gpu_arch = gpu.split(":")
                        if args.lookup is None:
                            pci_id_data["pci_id_data"][f"{vendor_id}:{device_id}"] = gpu_arch
                        elif args.lookup == f"{vendor_id}:{device_id}":
                            print(f"{vendor_id}:{device_id}    {device_name}")
                        add_subdevices = True
                        break

    # Print the json data
    if args.lookup is None:
        print(json.dumps(pci_id_data, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lookup", type=str, default=None, metavar="1234:abcd", help="Look up PCI id")
    parser.add_argument("filename", nargs="?", default="pci.ids", help="pci.ids filename (optional)")
    args = parser.parse_args()

    # Process the input file and output to the SQLite database
    process_pci_file(args)
