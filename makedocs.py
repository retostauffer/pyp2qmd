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
import mydocstring                  # Parsing functions and classes (extracting docstring)
import docstring_parser             # Parsing docstring

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
    parser.add_argument("-o", "--output_dir", type = str, default = "_quarto",
            help = "Name of the output directory to store the qmd file")
    parser.add_argument("--overwrite", default = False, action = "store_true",
            help = "Only used if action = create; will overwrite _quarto.yml if needed.")
    parser.add_argument("--man_dir", type = str, default = "man",
            help = "Folder to store the function/class manuals qmds, " + \
                    "ceated inside the --output_dir folder. Must start with [A-Za-z].")
    parser.add_argument("--docstringstyle", type = str, default = "GOOGLE",
            help = "Docstring type (format).")
    parser.add_argument("--include_hidden", default = False, action = "store_true",
            help = "If set, hidden functions and methods will also be documented " + \
                    "(functions/methods starting with _ or __)")

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
                 f"but the file \"{ymlfile}\" " + \
                 f"already exists. Remove folder \"{args.output_dir}\" or use " + \
                 f"--overwrite; be aware, will overwrite the existing \"{ymlfile}\".")

    if not re.match("^[A-Za-z]", args.man_dir):
        parser.print_help()
        sys.exit(f"\nUsage error: man_dir must start with [A-Za-z].")

    return args


def create_quarto_yml(args):
    """

    Returns:
    bool: Returns `True` if the yml file is created the first time
    by calling this function, else `False` (file did already exist).
    """
    import os
    ymlfile = f"{args.output_dir}/_quarto.yml"

    if args.action == "init":
        res = True
        # If yml already exists and overwrite = False, error
        if os.path.isfile(ymlfile) and not args.overwrite:
            raise Exception(f"action = {args.action}, overwrite = {args.overwrite} " + \
                    f"but file \"{ymlfile}\" already exists; stop!")

        # If output directory does not yet exist, create.
        if not os.path.isdir(args.output_dir):
            try:
                os.makedirs(args.output_dir)
            except:
                raise Exception(f"Unable to create output folder \"{args.output_dir}\"")

        # Content of the yml file
        content = {"project": {"type": "website"},
                     "website": {"title": args.package,
                        "navbar": {"search": True,
                            "right": [{"icon": "github", "href": "https://github.com/dummy/entry", "aria-label": "gsdata GitHub"}]},
                        "sidebar": {"collapse-level": 1,
                           "contents": [{"text": "Home", "file": "index.qmd"}]
                        }
                     },
                     "format": {"html": {"theme": ["quarto", "pyp.scss"]}},
                     "execute": {"cache": True}
                   }

        # Else create (overwrite) the file
        with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))

    # Else (not init): Ensure the output folder and the yml file exists, else
    # init must be used.
    else:
        res = False
        if not os.path.isdir(args.output_dir):
            raise Exception(f"Output folder \"{args.output_dir}\" does not exist. " + \
                    "You may first need to call the script with action = init")
        elif not os.path.isfile(ymlfile):
            raise Exception(f"yml file \"{ymlfile}\" does not exist. " + \
                    "You may first need to call the script with action = init")

    # Create references dir if not existing
    refdir = os.path.join(args.output_dir, args.man_dir)
    if not os.path.isdir(refdir):
        try:
            os.makedirs(refdir)
        except Exception as e:
            raise Exception(e)

    return res


def write_sass(args):
    """
    Write sass
    """
    import os
    scssfile = f"{args.output_dir}/pyp.scss"
    if not os.path.isfile(scssfile) or args.action == "init":
        # Sorry, indent is important
        content = """
/*-- scss:defaults --*/
// Base document colors
$body-bg: white;
$body-color: black;
//$link-color: #75AADB;
$link-color: #4287f5;

/*-- scss:custom --*/
// Styling of the <dl> lists
dl.pyp-list {
    dd {
        margin-left: 2em;
    }
}
        """
        with open(scssfile, "w+") as fid:
            fid.write(content)


def update_quarto_yml(args, section, mans):

    import yaml

    assert isinstance(section, str)
    assert isinstance(mans, list)
    assert all([isinstance(x, str) for x in mans])
    ymlfile = f"{args.output_dir}/_quarto.yml"

    # Read existing 
    with open(ymlfile, "r") as fid:
        content = yaml.load("".join(fid.readlines()), yaml.SafeLoader)

    # Dictionary to extend the content
    tmp = {'section': section,
           'contents': [{"text": x, "file": f"{args.man_dir}/{x}.qmd"} for x in mans]}

    # Append and overwrite _quarto.yml with new content
    content["website"]["sidebar"]["contents"].append(tmp)
    with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))


class manPage:
    def __init__(self, package, typ, name, docstrings):
        if not isinstance(package, str):
            raise TypeError("argument `package` must be str (package name)")
        if not isinstance(typ, str):
            raise TypeError("argument `typ` must be str")
        elif not typ in ["function", "class"]:
            raise ValueError("argument `typ` must be \"function\" or \"class\"")
        if not isinstance(name, str):
            raise TypeError("argument `name` must be str (original class or function name)")

        # Store args
        self._package    = package
        self._name       = name
        self._typ        = typ
        self._docstrings = docstrings

        # Checking docstrings input
        self._check_docstrings_input(docstrings)

    def _check_docstrings_input(self, x):
        """_check_docstrings_input(x)

        Checking user input when initializing object of class manPage

        Args:
            x: dictionary of dictionaries containing the Docstring extracted
                via docstring_parser and the Signature extracted via inspect.

        Returns:
            No return, will throw errors if the user's input is incorrect.
        """
        arg = "docstrings"
        if not isinstance(x, dict):
            raise TypeError(f"argument `{arg}` must be dict")
        for key,rec in x.items():
            print(f"[DEVEL] input test for {key}")
            if not isinstance(rec, dict):
                raise TypeError(f"elements in `{arg}` must be dict")
            elif not "docstring" in rec.keys() or not "signature" in rec.keys():
                raise ValueError(f"dictionaries in `{arg}` must contain \"docstring\" and \"signature\"")
            elif not isinstance(rec["docstring"], docstring_parser.common.Docstring):
                raise TypeError(f"\"docstring\" must inherit docstring_parser.common.Docstring")
            elif not isinstance(rec["signature"], inspect.Signature):
                raise TypeError(f"\"signature\" must inherit inspect.Signature")

    def get(self, attr, name = None):
        """get(attr, name = None)

        Args:
            attr (str): attribute to extract from the docstring.
            name (None, str): The function or class name for which the
                attribute should be extracted. If None: name with which
                the object has been initialized (main function/class).

        Return:
            Returns the attribute from the docstring, type depends on
            what is stored in docstring_parser.common.Docstring.
        """
        if name is None: name = self._name
        assert isinstance(name, str), "name must be string"
        assert isinstance(attr, str), "attr must be string"
        res = getattr(self._docstrings[name]["docstring"], attr)

        if attr in ["short_description", "long_description"] and res is not None:
            import re

            # Replace sphinx refs with quarto refs
            matches = re.findall(r":py:(?:func|class):`.*?`", res)
            for m in matches:
                print(f" >>>>>>>>>> {m}")
                qmd = re.search("(\w+)(?=`)", m).group(1)
                txt = re.search("`(.*?)(?=`)", m).group(1)
                res = res.replace(m, f"[{txt}]({qmd}.qmd)")


        return res

    def signature(self, name = None):
        """signature(name = None)

        Args:
            name (None, str): The function or class name for which the
                attribute should be extracted. If None: name with which
                the object has been initialized (main function/class).

        Return:
            (str) Returns signature as string.
        """
        if name is None: name = self._name
        assert isinstance(name, str), "attr must be string"
        return str(self._docstrings[name]["signature"]) # str(inspect.Signature)

    def _repr_args(self):
        res = "<dl class=\"pyp-list param-list\">\n"
        for arg in self.get("params"):
            short_arg = re.search("^([\*\w]+)", arg.args[1]).group(1).replace("*", "")
            # Building html table row
            res += "  <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                   f"   <code id=\"{self._package}_:_{short_arg}\">{arg.args[1]}</code>\n" + \
                   "  </dt>\n" + \
                   f" <dd>{arg.description}</dd>\n"

        return res + "</dl>"

    def __repr__(self):
        res  = "## " + self.get("short_description") + " {.unnumbered}\n\n"

        if self.get("long_description"):
            res += "### Description\n\n"
            res += self.get("long_description")
        #else:
        #    res += "WARNING(long_description missing)"

        res += "\n\n### Usage\n\n"
        res += "<pre><code class='language-python'>" + \
               f"{self._name}{self.signature()}" + \
               "</code></pre>"

        # Function arguments
        res += "\n\n### Arguments\n\n"
        res += self._repr_args()

        # Return value
        if self.get("returns"):
            res += "\n\n### Return\n\n"
            res += f"{self.get('returns').description}"

        # If is class, append methods
        if self._typ == "class" and len(self._docstrings) > 1:

            res += "\n\n### Methods\n\n"

            res += "<dl class=\"pyp-list method-list\">\n"
            for key,rec in self._docstrings.items():
                # Skipping main class
                if key == self._name: continue
                res += "    <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                       f"       <code>{key}{self.signature(key)}</code>\n    </dt>\n"
                tmp = self.get('short_description', key)
                if tmp is None:
                    tmp = "WARNING(short_description missing)"
                else:
                    tmp = re.sub(f"^{key}", "", tmp)
                res += f"    <dd>{tmp}</dd>\n"
            res += "</dl>\n"

        res += "\n\n### Examples\n\n"
        res += "```{python}\n"
        res += "#| echo: true\n"
        res += "#| error: true\n"
        res += "#| warning: true\n"

        # Adjusting source code to be valid quarto python code
        tmp = "\n".join([x.description for x in self.get("examples")])
        # Comment 'text' (can be included in the py example section)
        tmp = re.sub(r"^(?!(>>>))", "## ", tmp, flags = re.MULTILINE)
        # Removing empty lines
        tmp = re.sub(r"^##\s+?$", "", tmp, flags = re.MULTILINE)
        # Remove >>> code identifiers
        res += re.sub(r"^>>>\s+?", "", tmp, flags = re.MULTILINE)
        res += "\n```"
        res += "\n"

        return res

# Testing a function
def py2quarto(x, include_hidden = False):
    """py2quarto(x)

    Args:
        x: tuple where the first element is a str, the second
            element a function or class.
        include_hidden (bool): Defaults to `False`. If set,
            hidden functions and methods (_*, __*) will also
            be documented.
    """
    if not isinstance(x, tuple):
        raise TypeError("argument `x` must be a tuple")
    elif not len(x) == 2:
        raise TypeError("tuple on argument `x` must be of length 2")
    elif not isinstance(x[0], str):
        raise TypeError("first element of tuple `x` must be str")
    if not isinstance(include_hidden, bool):
        raise TypeError("argument `include_hidden` must be boolean True or False")

    # Checking function or class
    if not inspect.isfunction(x[1]) and not inspect.isclass(x[1]):
        raise TypeError("second element of tuple `x` must be function or class")

    def extract_docstrings(obj, style, include_hidden):
        dstyle = getattr(docstring_parser.DocstringStyle, style.upper())

        # Extract class docstring
        docstrings = {}
        class_docstring = docstring_parser.parse(inspect.getdoc(obj), dstyle)
        if class_docstring:
            docstrings[obj.__name__] = {"docstring": class_docstring,
                                        "signature": inspect.signature(obj)}
        
        # Extract method/function docstrings
        for name, func in inspect.getmembers(obj):
            if not include_hidden and name.startswith("_"):
                continue
            # Else check if is function
            if inspect.isfunction(func):
                sig = inspect.signature(func)
                try:
                    doc = docstring_parser.parse(inspect.getdoc(func), dstyle)
                except Exception as e:
                    print(f"Problem extracting docstring from:   {name}")
                    raise Exception(e)
                docstrings[name] = {"docstring": doc, "signature": sig}
        
        return docstrings

    docstrings = extract_docstrings(x[1], args.docstringstyle, include_hidden)

    # Generate manPage object
    u = manPage(package    = args.package,
                typ        = "function" if inspect.isfunction(x[1]) else "class",
                name       = x[0],
                docstrings = docstrings)

    # Returning object of class manPageFunction or manPageClass
    return u


# -------------------------------------------------
# -------------------------------------------------
if __name__ == "__main__":

    # Parsing user args
    args = parse_input_args()

    # If args.action is init, crate _quarto.yml
    yml_newly_created = create_quarto_yml(args)

    # Wirte sass
    write_sass(args)

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
    print("\n\n")


    #test = py2quarto(funs[0])
    #test2 = py2quarto(clss[0])
    #print(test)
    #sys.exit(" ------ reto exit -----------")

    # -------------------------------------------------
    # Create man pages for functions
    # -------------------------------------------------
    man_func_created = []
    for fun in funs:
        man = py2quarto(fun, args.include_hidden)
        qmdfile = os.path.join(args.output_dir, args.man_dir, f"{fun[0]}.qmd")
        with open(qmdfile, "w+") as fid:
            print(man, file = fid)
        man_func_created.append(fun[0])
    man_func_created.sort()
    print(f"{man_func_created=}")

    # Adding Function references to _quarto.yml
    if yml_newly_created and len(man_func_created) > 0:
        update_quarto_yml(args, "Function reference", man_func_created)

    # -------------------------------------------------
    # Create man pages for classtions
    # -------------------------------------------------
    man_class_created = []
    for cls in clss:
        man = py2quarto(cls, args.include_hidden)
        qmdfile = os.path.join(args.output_dir, args.man_dir, f"{cls[0]}.qmd")
        with open(qmdfile, "w+") as fid:
            print(man, file = fid)
        man_class_created.append(cls[0])
    man_class_created.sort()
    print(f"{man_class_created=}")

    test = py2quarto(clss[1])
    print(test)

    # Adding Function references to _quarto.yml
    if yml_newly_created and len(man_class_created) > 0:
        update_quarto_yml(args, "Class reference", man_class_created)

