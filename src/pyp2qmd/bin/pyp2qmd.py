#!/usr/bin/env python

def main():
    from pyp2qmd import Config, DocConverter
    config  = Config(argparse = True)
    print(config)
    docconv = DocConverter(config)
    print(docconv)

if __name__ == "__main__":
    main()
