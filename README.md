# softwipe
A tool for automatically checking the software quality of a C/C++ program and giving it a score. It is developed as part of my Hiwi project at the Heidelberg Institute for Theoretical Studies (HITS). The background for doing this is the appearent lack of quality in evolutionary biology software as found in this paper: https://academic.oup.com/mbe/article/35/5/1037/4828033

Softwipe runs various checks to produce a software quality score: it compiles your program using clang and checks for compiler warnings; it activates almost all available warnings here. It runs your program with clang sanitizers activated, which detect memory errors and undefined behavior. It checks for the usage of assertions. It runs the following static code analyzers: cppcheck, clang-tidy, KWStyle, and lizard. Lizard is also used to find your programs average cyclomatic complexity and code duplication.

## Dependencies
This tool runs a bunch of other tools that must be installed:
* Clang (<https://clang.llvm.org>, probably available in your package manager)
* cppcheck (<http://cppcheck.sourceforge.net>, probably available in your package manager)
* clang-tidy (part of LLVM tools (<http://llvm.org>); either clang-tidy is available in your package manager as a standalone (e.g. in apt-get it is), or your package manager includes it in LLVM (e.g. in homebrew this is the case))
* Lizard (<https://github.com/terryyin/lizard>, available in pip)
* KWStyle (<https://kitware.github.io/KWStyle/>)

For make-based projects, you also need:
* compiledb (<https://github.com/nickdiego/compiledb-generator>, available in pip)

Also, if the program you want to check uses make oder CMake as build system, make and CMake must be installed respectively.

For macOS and Debian-based systems, softwipe can automatically install these dependencies for you. Just run softwipe; if a dependency cannot be found, it will ask you whether it should automatically install it. Note for Mac users: Homebrew must be installed for the automatic installation of dependencies.

## Installation & Usage

Clone this repository to download softwipe:
```
git clone https://github.com/adrianzap/softwipe.git
```

#### Basic usage
Softwipe can be run as follows:
```
softwipe.py [-c | -C] [-M | -m | -l target [target ...]] [-e EXECUTEFILE] programdir
```
Where:

`-c` tells softwipe that your program is C, and `-C` tells softwipe that you program is C++.

`-M` tells softwipe to build your program using CMake, `-m` using make, and `-l` using clang. The `-l` option takes as arguments the files to compile.

`-e` specifies the path to an "execute file" which contains a command line that executes your program.

`programdir` specifies the root directory of your target program.

Example command line for a CMake-based C++ program:
```
softwipe.py -CM path/to/program -e path/to/executefile
```

For more options and further information, run `softwipe.py --help`.
