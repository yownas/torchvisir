"""Very simple demonstration of torchvisir"""

from torchvisir.torchvisir import Torchvisir

tv = Torchvisir()

print(f"### No target:}")
print("### Dry-run install:")
print(tv.install_torch(target=[], dry_run=True))

print("")

tv.pci_ids = ["10de:2b85"] # Insert a fake RTX 5090
print(f"### Target for faked RTX 5090: {tv.get_torch_targets()}")
print("### Dry-run install:")
print(tv.install_torch(dry_run=True))

print("")

print("### Multiple targets:")
pci_mix = [
    (["10de:1b80", "10de:2b85"], "Mixed NVIDIA generations: GTX 1080 + RTX 5090 → cu126 + cu130"),
    (["8086:7d55", "10de:2684"], "Typical laptop: Intel iGPU + NVIDIA dGPU: Meteor Lake Arc iGPU + RTX 4090 → xpu + cu130"),
    (["1002:150e", "10de:2684"], "AMD APU + NVIDIA dGPU: Strix 890M + RTX 4090 → gfx1150 + cu130"),
    (["1002:744c", "8086:e20b"], "AMD + Intel: RX 7900 XTX + Arc B580 → gfx1100 + xpu"),
    (["10de:2b85", "1002:7550", "8086:e20b"], "Three vendors: cu130 + gfx1201 + xpu"),
]
for test in pci_mix:
    tv.pci_ids = test[0]
    print(f"  # {test[1]} ({tv.get_torch_targets()})")
    print(f"  {tv.install_torch(dry_run=True)}")
    print("")

print("### Dry-run forced reinstall for target 'gfx1201', AMD Radeon RX 9070:")
print(tv.install_torch(target=['gfx1201'], force_reinstall=True, dry_run=True))

print("")
# Add an imaginary GPU to the db
tv.data['pci_id_data']['ffff:ffff'] = 'visir-gpu123'
# Add repository information
tv.data['repos']['VisirGPUs'] = {
    "pattern": "^visir-gpu",
    "index_url": "https://localhost/visir-whl/",
       "pkgs": [
            "torch==2.14.0+my_vgpu",
            "torchvision==0.29.0+my_vgpu",
            "torchaudio==2.11.0.3+my_vgpu"
        ]
    }
# The data above can also be added with tv.load_data(folder="/some/path/my_data_folder")
tv.pci_ids = ["ffff:ffff"] # Pretend we detected our fake GPU
print("### Dry-run install a fake GPU")
print(tv.install_torch(dry_run=True))

print("")

# Minimal dry-run example
# Torchvisir().install_torch(dry_run=True)

print("### Dry-run test with real lookup")
# This does the same as above, but show each step
tv.get_pci_ids() # Get the list of real PCIe devices on the system
print(f"### Found {len(tv.pci_ids)} PCIe devices")
print(f"### Targets: {tv.get_torch_targets()}")
print("### Dry-run install:")
print(tv.install_torch(dry_run=True))

