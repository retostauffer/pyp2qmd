#!/usr/bin/env python

def main():
    from os.path import join, basename, dirname
    from pyp2qmd import Config, DocConverter
    from shutil import copy

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

    # Copy file
    src = join(abspath, "github-mark.svg")
    copy(src, join(config.get("quarto_dir"), "github-mark.svg"))

    # Adding favicon
    repo_url    = "https://github.com/retostauffer/pyp2qmd"
    repo_branch = "main"
    docconv.add_favicon(join(abspath, "favicon.png"))
    docconv.add_repo_url(repo_url, repo_branch)
    docconv.add_issue_url("https://github.com/retostauffer/pyp2qmd/issues")

    docconv.add_navbar_right({"icon": "github", "href": f"{repo_url}/tree/{repo_branch}"})


if __name__ == "__main__":
    main()
