#!/usr/bin/env python

def main():
    from pyp2qmd import Config, DocConverter

    # Initialize Config; parses user arguments via argparse
    config  = Config(argparse = True)
    if not config.get("silent"): print(config)

    # Initialize DocConverter; creates _quarto.yml,
    # pyp.sass, and index.qmd if needed.
    docconv = DocConverter(config)
    if not config.get("silent"): print(docconv)

    print(config)
    if config.get("action") == "examples":
        docconv.examples()
    else:
        docconv.document()
        docconv.update_quarto_yml()

if __name__ == "__main__":
    main()
