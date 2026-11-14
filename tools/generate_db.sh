#!/bin/sh

# Get files
curl --silent --output=pci.ids https://raw.githubusercontent.com/pciutils/pciids/refs/heads/master/pci.ids

python pciid2json.py > db/gpus.json

echo "Diff:"
diff ../torchvisir/tvdb/gpus.json db/gpus.json 

mv db/gpus.json ../torchvisir/tvdb/.
