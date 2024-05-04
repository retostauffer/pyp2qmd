#!/usr/bin/env python3



import pyp2qmd

config   = pyp2qmd.Config(argparse = True)
print(config)
#config   = pyp2qmd.Config()
#config.setup(action = "document", package = "colorspace")

worker = pyp2qmd.DocConverter(config)
print(worker)

#parser = pyp2qmd.Parser()
