#!/usr/bin/env python

def main():
    from pyp2qmd import Config, DocConverter

    # Initialize Config; parses user arguments via argparse
    config  = Config(argparse = True)
    print(config)

    # Initialize DocConverter; creates _quarto.yml,
    # pyp.sass, and index.qmd if needed.
    docconv = DocConverter(config)

    print(docconv)

    # Documenting classes only (testing)
    docconv.document_classes()

if __name__ == "__main__":
    main()
