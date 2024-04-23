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
import argparse
import inspect
import mydocstring

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
    allowed_action = ["initialize", "document"]

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

    # Parsing input args
    args = parser.parse_args()

    args.action = args.action[0]
    if not args.action in allowed_action:
        parser.print_help()
        sys.exit("\nUsage error: invalid \"action\" (see help).")

    if args.package is None:
        parser.print_help()
        sys.exit("\nUsage error: argument -p/--package must be set.")
    elif 

    ymlfile = f"{args.output_dir}/_quarto.yml"
    if args.action == "create" and isfile(ymlfile):
        parser.print_help()
        sys.exit(f"\nUsage error: action is set to \"{args.action}\" " + \
                "but file \"{ymlfile}\" " + \
                "already exists. Remove folder \"{args.output_dir}\" or use " + \
                "--overwrite; be aware, will overwrite the existing \"{ymlfile}\".")

    return args

# -------------------------------------------------
# -------------------------------------------------
if __name__ == "__main__":

    # Parsing user args
    args = parse_input_args()
    print(args)
    sys.exit(3)


    import colorspace
    import inspect
    funs = inspect.getmembers(colorspace, inspect.isfunction)
    clss = inspect.getmembers(colorspace, inspect.isclass)

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



