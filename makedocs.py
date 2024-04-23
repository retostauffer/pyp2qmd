#!/usr/bin/env python3
# -------------------------------------------------
# Building quarto manual pages for python package
# -------------------------------------------------

### Tutorial
##extract = mydoc.extract.PyExtract(source)
##add = extract.extract('add')

import sys
import os
import re
import yaml
import re
import argparse
from importlib import import_module # Dynamic module import
import inspect                      # Find functions/classes in package
import mydocstring                  # Parsing docstrings

class docParser:
    def __init__(self, file):
        if not isinstance(file, str):
            raise TypeError("argument `file` must be str")
        if not os.path.isfile(file):
            raise FileNotFoundError(f"file \"{file}\" not found")

        try:
            with open(file, "r") as fid:
                self._src = "".join(fid.readlines())
        except Exception as e:
            raise Exception(e)

        # Find functions
        fun = self.find_functions()

    def find_functions(self):
        pattern = re.compile(r"^def\s(.*)(?=(\())", re.M)
        function_names = []
        for rec in pattern.findall(self.source()):
            function_names.append(rec[0])

        print(f"[DEV] {function_names=}")
        return function_names

        
    def source(self):
        return self._src

def parse_input_args():

    # Allowed action options
    allowed_action = ["init", "document"]

    import argparse
    parser = argparse.ArgumentParser("Creating qmd documentation from python package")
    parser.add_argument("action", nargs = 1, type = str,
            help = f"Action to perform, one of: {', '.join(allowed_action)}")
    parser.add_argument("-p", "--package", type = str,
            help = "Name of the python package.")
    parser.add_argument("-o", "--output_dir", type = str, default = "docs",
            help = "Name of the output directory to store the qmd file")
    parser.add_argument("--overwrite", default = False, action = "store_true",
            help = "Only used if action = create; will overwrite _quarto.yml if needed.")
    parser.add_argument("--references_dir", type = str, default = "references",
            help = "Folder to store the function/class reference qmds, " + \
                    "ceated inside the --output_dir folder. Must start with [A-Za-z].")

    # Parsing input args
    args = parser.parse_args()

    args.action = args.action[0]
    if not args.action in allowed_action:
        parser.print_help()
        sys.exit("\nUsage error: invalid \"action\" (see help).")

    if args.package is None:
        parser.print_help()
        sys.exit("\nUsage error: argument -p/--package must be set.")

    ymlfile = f"{args.output_dir}/_quarto.yml"
    if args.action == "create" and isfile(ymlfile):
        parser.print_help()
        sys.exit(f"\nUsage error: action is set to \"{args.action}\" " + \
                "but file \"{ymlfile}\" " + \
                "already exists. Remove folder \"{args.output_dir}\" or use " + \
                "--overwrite; be aware, will overwrite the existing \"{ymlfile}\".")

    if not re.match("^[A-Za-z]", args.references_dir):
        parser.print_help()
        sys.exit(f"\nUsage error: references_dir must start with [A-Za-z].")

    return args


def create_quarto_yml(args):
    import os
    ymlfile = f"{args.output_dir}/_quarto.yml"

    if args.action == "init":
        # If yml already exists and overwrite = False, error
        if os.path.isfile(ymlfile) and not args.overwrite:
            raise Exception("action = {args.action}, overwrite = {args.overwrite} " + \
                    "but file \"{ymlfile}\" already exists; stop!")

        # If output directory does not yet exist, create.
        if not os.path.isdir(args.output_dir):
            try:
                os.makedirs(args.output_dir)
            except:
                raise Exception(f"Unable to create output folder \"{args.output_dir}\"")

        # Content of the yml file
        ymlcontent = {"project":
                            {"type": "website"},
                      "website": [
                          {"title": f"{args.package} documentation"},
                          {"navbar":
                              {"left":
                                [{"href": "index.qmd", "text": "Home"},
                                 "about.qmd"]
                              },
                          }
                      ], # End Website
                      "format":
                          {"html":
                                  [{"theme": "cosmo",
                                    "css": "style.css",
                                    "toc": "true"}]
                          } # end html
                      }

        # Else create (overwrite) the file
        with open(ymlfile, "w+") as fid: fid.write(yaml.dump(ymlcontent))

    # Else (not init): Ensure the output folder and the yml file exists, else
    # init must be used.
    else:
        if not os.path.isdir(outdir):
            raise Exception(f"Output folder \"{outdir}\" does not exist. " + \
                    "You may first need to call the script with action = init")
        elif not os.path.isfile(ymlfile):
            raise Exception(f"yml file \"{ymlfile}\" does not exist. " + \
                    "You may first need to call the script with action = init")

    # Create references dir if not existing
    refdir = os.path.join(args.output_dir, args.references_dir)
    if not os.path.isdir(refdir):
        try:
            os.makedirs(refdir)
        except Exception as e:
            raise Exception(e)


# -------------------------------------------------
# -------------------------------------------------
if __name__ == "__main__":

    # Parsing user args
    args = parse_input_args()

    # If args.action is init, crate _quarto.yml
    create_quarto_yml(args)

    # Trying to import the module
    try:
        pkg = import_module(args.package)
    except Exception as e:
        raise Exception(e)

    # Extracting functions and classes
    import inspect
    funs = inspect.getmembers(pkg, inspect.isfunction)
    clss = inspect.getmembers(pkg, inspect.isclass)

    functions = [x[0] for x in funs]
    classes   = [x[0] for x in clss]
    print(f"{functions=}")
    print(f"{classes=}")


    for fun in funs:
        print(f"Function: {fun[0]}")
        tmp = mydocstring.extract.PyExtract(inspect.getsource(fun[1]))
    for cls in clss:
        print(f"Class:    {cls[0]}")
        for ff in inspect.getmembers(cls[1], inspect.isfunction):
            if ff[0].startswith("_"):
                print(f"    - ( {ff[0]} )")
            else:
                print(f"    - {ff[0]}")


    # Testing a function

    fun = funs[1]
    print(fun)



