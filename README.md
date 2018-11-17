# softwipe
A tool for automatically checking the software quality of a C/C++ program. It is developed as part of my Hiwi project at the Heidelberg Institute for Theoretical Studies (HITS). The background for doing this is the appearent lack of quality in evolutionary biology software as found in this paper: https://academic.oup.com/mbe/article/35/5/1037/4828033

## Dependencies
This tool runs a bunch of other tools that must be installed:
* Clang (<https://clang.llvm.org>, probably available in your package manager)
* cppcheck (<http://cppcheck.sourceforge.net>, probably available in your package manager)
* clang-tidy (part of LLVM tools (<http://llvm.org>); either clang-tidy is available in your package manager as a standalone (e.g. in apt-get it is), or your package manager includes it in LLVM (e.g. in homebrew this is the case))
* Lizard (<https://github.com/terryyin/lizard>, available in pip)

For make-based projects, you also need:
* compiledb (<https://github.com/nickdiego/compiledb-generator>, available in pip)

Also, if the program you want to check uses make oder CMake as build system, make and CMake must be installed respectively.
