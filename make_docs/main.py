#!/usr/bin/env python

def main():
    from os.path import join, basename
    from pyp2qmd import Config, DocConverter

    # Initialize Config; parses user arguments via argparse
    config  = Config()
    config.setup(action = "init", package = "pyp2qmd", overwrite = True)

    # Initialize DocConverter; creates _quarto.yml,
    # pyp.sass, and index.qmd if needed.
    docconv = DocConverter(config)

    docconv.document()
    docconv.update_quarto_yml()

    # Adding test page
    src = join("make_docs", "getting_started.qmd")
    docconv.navbar_add_page(src, basename(src), "Getting started")
    src = join("make_docs", "design_philosophy.qmd")
    docconv.navbar_add_page(src, basename(src), "Design philosophy")

if __name__ == "__main__":
    main()
