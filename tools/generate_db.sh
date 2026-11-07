#!/bin/sh

# Get files
curl --output=data/pci.ids https://raw.githubusercontent.com/pciutils/pciids/refs/heads/master/pci.ids

python pciid2json.py data/pci.ids | tee db/gpus.json
