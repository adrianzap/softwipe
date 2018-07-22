# crapware_checker
A tool for automatically checking the software quality of a C/C++ program. It is developed as part of my Hiwi project at the Heidelberg Institute for Theoretical Studies (HITS). The background for doing this is the appearent lack of quality in evolutionary biology software as found in this paper: https://academic.oup.com/mbe/article/35/5/1037/4828033

## Dependencies
This tool runs a bunch of other tools that must be installed:
* Clang (<https://clang.llvm.org>, probably available in your package manager)
* cppcheck (<http://cppcheck.sourceforge.net>, probably available in your package manager)
* splint (<http://www.splint.org>, probably available in your package manager)
* flawfinder (<https://www.dwheeler.com/flawfinder/>, available in pip)
* clang-tidy (part of LLVM tools (<http://llvm.org>), LLVM is probably available in your package manager)
* cqmetrics (<https://github.com/dspinellis/cqmetrics>)

Also, if the program you want to check uses make oder CMake as build system, make and CMake must be installed respectively.
