#!/usr/bin/env python

def main():
    from os.path import join, basename, dirname
    from pyp2qmd import Config, DocConverter

    # Get path to this file
    abspath = dirname(__file__)

    # Initialize Config; parses user arguments via argparse
    config  = Config()
    config.setup(action = "init", package = "pyp2qmd", overwrite = True)

    # Initialize DocConverter; creates _quarto.yml,
    # pyp.sass, and index.qmd if needed.
    docconv = DocConverter(config)

    docconv.document()
    docconv.update_quarto_yml()

    # Adding test page
    src = join(abspath, "getting_started.qmd")
    docconv.add_navbar_page(src, basename(src), "Getting started")
    src = join(abspath, "design_philosophy.qmd")
    docconv.add_navbar_page(src, basename(src), "Design philosophy")

    # Adding favicon
    docconv.add_favicon(join(abspath, "favicon.png"))

if __name__ == "__main__":
    main()
