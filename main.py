#!/usr/bin/env python3
import zono.colorlogger as cl
import subprocess
import argparse
import json
import time
import os
import sys


def get_file(filename):
    return os.path.join(os.path.dirname(__file__), filename)


def create_output_file(path):
    return os.path.join(
        os.path.dirname(path), os.path.splitext(os.path.basename(path))[0]
    )


def wrap_command(command, file_path, output_path):
    return (
        command.replace("{file_output}", f"{file_path} -o {output_path}")
        .replace("{file_path}", file_path)
        .replace("{output_file}", output_path)
    )


def get_full_file_path(file_path):
    if os.path.isabs(file_path):
        return file_path
    else:
        return os.path.abspath(file_path)


def log(message, *args, func=cl.log, **kwargs):
    global VERBOSE
    if VERBOSE:
        func(message, *args, **kwargs)


def form_language(language):
    if language.startswith("."):
        return language.replace(".", "", 1)
    return "." + language


def load_languages():
    with open(get_file("languages.json"), "r") as f:
        _languages = json.load(f)

    filetypes = {}
    languages = _languages.copy()
    for lang, info in _languages.items():
        info["name"] = lang
        for inf in info["file-types"]:
            filetypes[inf] = info
        for alias in info["aliases"]:
            languages[alias] = info

    return languages, filetypes


def get_language(args, parser):
    file_path = args.file
    languages, filetypes = load_languages()

    full_dict = languages.copy()
    full_dict.update(filetypes)

    file_sp = os.path.splitext(os.path.basename(file_path))
    if args.language is not None:
        args.language = args.language.lower()
        language = full_dict.get(
            args.language, full_dict.get(form_language(args.language))
        )
        if language is None:
            parser.error(f"Language {args.language} does not exist")
            return

    else:
        file_type = file_sp[1]
        if file_type == "" and os.access(file_path, os.X_OK):
            return languages["executable"]

        language = filetypes.get(file_type, None)
        if language is None:
            parser.error(f"Language {file_type} does not exist")
            return

    return language


def get_compiler(args, parser):
    file_path = args.file
    language = get_language(args, parser)

    if language["compiled"] is not True:
        parser.error(f'Language: {language["name"]} is not a compiled language')
        return
    if args.compiler_args is not None:
        args = args.compiler_args
    else:
        args = language["default-args"] + " " + args.args

    output_path = create_output_file(file_path)
    return (
        wrap_command(language["compiler-command"], file_path, output_path) + " " + args
    )


def compile_and_run(args, parser, language, run_args, new=False):
    file_path = args.file
    output_file = create_output_file(file_path)
    if new is False:
        log(f"Compiling {os.path.basename(file_path)} due to changes found in file")
    else:
        log(
            f"Compiling {os.path.basename(file_path)} because there is no existing executable"
        )

    if compile_file(args, parser, log):
        cmd = (
            wrap_command(language["run-command"], args.file, output_file)
            + " "
            + run_args
        )

        return run_cmd(cmd, args)


def run_cmd(cmd, args):
    st = time.perf_counter()
    try:
        stat = subprocess.run(cmd, check=True, shell=True)
        returncode = stat.returncode
    except subprocess.CalledProcessError as e:
        et = time.perf_counter() - st
        cl.error(
            f"Error while running {args.file} process returned code: {e.returncode} in {et:.4}s"
        )
        return False
    except KeyboardInterrupt:
        return False
    else:
        et = time.perf_counter() - st
        print(f"Ran {args.file} returned status code {returncode} in {et:.4f}s")
        return True


def compile_file(args, parser, repr=print):
    cmd = get_compiler(args, parser)

    st = time.perf_counter()
    try:
        stat = subprocess.run(cmd, check=True, shell=True)
        returncode = stat.returncode
    except subprocess.CalledProcessError as e:
        returncode = e.returncode

    except KeyboardInterrupt:
        return False
    et = time.perf_counter() - st
    if returncode == 0:
        with open(get_file("store.json"), "r+") as f:
            store = json.load(f)
            store[args.file] = os.path.getmtime(args.file)
            f.seek(0)
            json.dump(store, f)

        repr(f"Compiled {args.file} with status code {returncode} in {et:.2f}s")
        return True
    else:
        cl.error(f"Error while compiling {args.file} returned status code {returncode}")
        return False


def compiler_args_type(arg_string):
    # Treat the entire argument string after "--compiler-args" as a single argument
    return [arg_string]


def parse_args():
    global VERBOSE

    parser = argparse.ArgumentParser(
        description="A simple command that can run any type of code",
        prog="run",
        usage="After + symbol all additional input will be passed in to the runtime of the file",
    )

    parser.add_argument("file", help="Path to input file")
    file_opts = parser.add_mutually_exclusive_group()
    file_opts.add_argument(
        "--language",
        help="Override and use different programming language instead of relying on filetype",
    )
    arg_opts = parser.add_mutually_exclusive_group()
    arg_opts.add_argument(
        "--compiler-args",
        help="Override and use custom arguments for the compiler",
        default=None,
    )
    arg_opts.add_argument(
        "-a", "--args", help="Add additional arguments to the compiler", default=""
    )
    mut_opts = parser.add_mutually_exclusive_group()
    mut_opts.add_argument(
        "--compile",
        action="store_true",
        help="Just compile the program without running it",
    )
    mut_opts.add_argument(
        "--run",
        action="store_true",
        help="Run the program without checking for changes",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Turns on verbose output"
    )

    if "+" in sys.argv:
        ind = sys.argv.index("+")
        run_args = sys.argv[ind + 1 :]
        sys.argv = sys.argv[:ind]
    else:
        run_args = []
    args = parser.parse_args()
    run_args = " ".join(run_args)

    VERBOSE = args.verbose
    args.inputfile = args.file
    args.file = get_full_file_path(args.file)
    if not os.path.exists(args.file):
        return parser.error(f"File {args.inputfile} does not exist")
    return args, parser, run_args


def main():
    if not os.path.exists(get_file("store.json")):
        with open(get_file("store.json"), "w") as f:
            json.dump({}, f)

    args, parser, run_args = parse_args()
    if args.compile:
        return compile_file(args, parser)
    elif args.run:
        language = get_language(args, parser)
        output_path = ""
        if "{output_file}" in language["run-command"]:
            output_path = create_output_file(args.file)
            if not os.path.exists(output_path):
                return parser.error(f"No existing binary for {args.file}")

        cmd = (
            wrap_command(language["run-command"], args.file, output_path)
            + " "
            + run_args
        )
        return run_cmd(cmd, args)

    language = get_language(args, parser)
    if language["compiled"] is not True:
        log("Language is not compiled running interpreter...")
        cmd = wrap_command(language["run-command"], args.file, "") + " " + run_args
        return run_cmd(cmd, args)

    output_path = create_output_file(args.file)
    if not os.path.exists(output_path):
        log(f"No existing binary for {args.file} creating a new one")
        return compile_and_run(args, parser, language, run_args, new=True)

    with open(get_file("store.json"), "r") as f:
        store = json.load(f)

    if args.file not in store:
        log(f"No existing entry for {args.file} treating it as a new file")
        return compile_and_run(args, parser, language, run_args, new=True)

    if os.path.getmtime(args.file) != store[args.file]:
        log(f"Detected changes in {args.file} recompiling the file")
        return compile_and_run(args, parser, language, run_args)

    cmd = wrap_command(language["run-command"], args.file, output_path) + " " + run_args
    run_cmd(cmd, args)


if __name__ == "__main__":
    main()
