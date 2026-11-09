<p align="center">
  <img width="526" height="522" alt="image" src="https://github.com/user-attachments/assets/23b9c4c7-3224-4b06-a5bb-7c7fddfc8368" />
</p>
The vegvísir (Icelandic for "wayfinder", lit. 'way shower') is an Icelandic magical stave intended to help the bearer
find their way through rough weather. The earliest known attestation is in the 1860 Huld manuscript. (Wikipedia)

# Torchvisir

Of the many horrors AI have brought upon us, one of the least talked about is having to install the correct version of pytoch
to match the GPU, operating system and application. This tool will hopefully take care of that.

# Usage

In the simplest form, all you need is this. This will detect PCI devices, load the default data and install torch with pip.

```
from torchvisir import Torchvisir

Torchvisir().install_torch()
```

If you prefer to do each step manually you can do that.

```
tv = Torchvisir()
tv.get_pci_ids()
tv.get_torch_targets()
tv.install_torch()
```

All data, and most of the logic, are saved as json. You can change or add devices as you wish.

Like adding your own PCI devices, a folder with json files or a python dict. Same with vendor repositories.

In normal cases ytou shouldn't need any of this, but you can poke at things if you really want to.

```
tv.load_data('my_folder_with/pci2taget-mappings/')
tv.data['pci_id_data']['ffff:ffff'] = 'visir-gpu123' # Imaginary GPU
tv.data['repos']['VisirGPUs'] = {
    "pattern": "^visir-gpu",
    "index_url": "https://localhost/visir-whl/",
       "pkgs": [
            "torch==2.14.0+my_vgpu",
            "torchvision==0.29.0+my_vgpu",
            "torchaudio==2.11.0.3+my_vgpu"
        ]
    }
tv.load_data('my_other_folder_with/repos')
tv.pci_ids = ["ffff:ffff"] # Pretend we detected our fake GPU
print(tv.install_torch(dry_run=True))
```

## TODO

Torchvisir is in early development, there are still a lot of things that needs to be fixed:

* CPU fallback
* Detect supported python versions
* Documentation
  
