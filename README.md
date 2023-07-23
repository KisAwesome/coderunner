# coderunner
A simple command that can run any type of code

Coderunner is a simple command-line utility that allows you to run any type of code by automatically detecting the programming language or by explicitly specifying the language. This tool is designed to streamline the process of compiling and running code with ease.

## Installation
Clone this repository to your local machine.
Make sure you have Python installed (version 3.6 or higher).
Install the required dependencies using pip:
```
pip install zono
```
## Usage
```
python3 main.py file_path [options] + [arguments for file]
```
The script takes the following arguments:

file_path: The path to the file containing the code you want to run.
Options
--language: Override the automatic language detection and specify the programming language explicitly.

--compiler-args: Override the default compiler arguments and provide custom arguments for the compiler.

-a, --args: Add additional arguments to the compiler.

--compile: Only compile the program without running it.

--run: Run the program without checking for changes.

-v, --verbose: Enable verbose output for more detailed information.

### Additional Arguments
After the + symbol in the command, you can provide additional arguments that will be passed to the runtime of the file being executed. These arguments will not be considered as options for the script.

## Examples
run a cpp program
```
python3 main.py test.cpp
```

run a python program pass in foo as argument
```
python3 main.py test.py + foo
```

run a cpp program with the file type .py and pass in foo as an argument
```
python3 main.py test.py --language cpp + foo
```

## Additional language support
Supporting additional programming languages in the  script can be achieved by adding their configurations to the languages.json file. The languages.json file serves as a lookup table, where each entry represents a specific programming language and its associated settings required for compilation and execution.

Let's break down the properties used in the configuration for each language:

"compiled" (boolean): Specifies whether the language requires compilation before execution. If set to true, the script will compile the code before running it.

"compiler-command" (string): The command used to compile the code. In this example, {file_output} is a placeholder that will be replaced with the output file name during the compilation process.

"default-args" (string): Default compiler arguments for the language. These arguments will be used unless overridden by the user using the --compiler-args option.

"run-command" (string): The command used to run the compiled code. In this example, {output_file} is a placeholder that will be replaced with the actual output file name generated during compilation.

"file-types" (list of strings): A list of file extensions associated with the language. The script will use these extensions to automatically detect the language based on the provided file path.

"aliases" (list of strings): An optional list of aliases for the language. Aliases can be used as an alternative way to specify the language when running the script. For example, if "c" has an alias "c-lang," you could use --language c-lang instead of --language c.

By adding the language configurations to the languages.json file, you can seamlessly support new languages without modifying the main coderunner.py script. This approach provides a clean and modular way to extend the capabilities of the script and makes it easier to maintain.

Example entry for the "c" language in languages.json:

```json
{
  "c": {
    "compiled": true,
    "compiler-command": "gcc {file_output}",
    "default-args": " -std=c17",
    "run-command": "{output_file}",
    "file-types": [".c"],
    "aliases": []
  }
}

```

## Ease of use
To make it easier to run the script with the name 'run' from any directory on your system, you can add the script to the system's PATH environment variable. By doing so, you can execute the script as if it were a system command, regardless of the current working directory.



