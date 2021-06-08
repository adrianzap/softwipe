# SoftWipe
A tool for automatically checking the software quality of a C/C++ program and giving it a score. It is developed as part of my Hiwi project at the Heidelberg Institute for Theoretical Studies (HITS). The background for doing this is the appearent lack of quality in evolutionary biology software as found in this paper: https://academic.oup.com/mbe/article/35/5/1037/4828033

SoftWipe runs various checks to produce a software quality score: it compiles your program using clang and checks for compiler warnings; it activates almost all available warnings here. It runs your program with clang sanitizers activated, which detect memory errors and undefined behavior. It checks for the usage of assertions. It runs the following static code analyzers: cppcheck, clang-tidy, KWStyle, and lizard. Lizard is also used to find your programs average cyclomatic complexity and code duplication.

## Installation & Usage

We developed and tested SoftWipe mainly on Ubuntu 20.04 LTS, some of the used code analysis tools might be affected on other OS versions.
Clone this repository to download SoftWipe:
```
git clone https://github.com/adrianzap/softwipe.git
```

#### Dependencies
There are some Python package dependencies, which need to be installed before running SoftWipe:
* numpy >= 1.17.4 (<https://numpy.org/>, can be installed using pip)
* scipy >= 1.3.3 (<https://www.scipy.org/>, can be installed using pip)

And there are also some tool dependencies, but fear not! For macOS and Debian-based systems, SoftWipe can automatically install the following dependencies for you. Just run SoftWipe (`sudo ./softwipe.py` - sudo is most likely required for installing the dependencies); if a dependency cannot be found, it will ask you whether it should automatically install it. Note for Mac users: Homebrew must be installed for the automatic installation of dependencies.

The following tools must be installed:
* Clang (<https://clang.llvm.org>, probably available in your package manager)
* cppcheck (<http://cppcheck.sourceforge.net>, probably available in your package manager)
* clang-tidy (part of LLVM tools (<http://llvm.org>); either clang-tidy is available in your package manager as a standalone (e.g. in apt-get it is), or your package manager includes it in LLVM (e.g. in homebrew this is the case))
* Lizard (<https://github.com/terryyin/lizard>, available in pip)
* KWStyle (<https://kitware.github.io/KWStyle/>)
* Infer (<https://github.com/facebook/infer>)

For make-based projects, you also need:
* compiledb (<https://github.com/nickdiego/compiledb-generator>, available in pip)

Also, if the program you want to check uses make oder CMake as build system, make and CMake must be installed respectively.

#### Conda
There is a conda package for SoftWipe, which can be installed using:
```
conda install softwipe -c angtft -c conda-forge
```
On the first execution of SoftWipe, it will install KWStyle, Lizard and Infer locally (as there are no conda packages for these tools yet).
We recommend installing SoftWipe in a separate conda environment, which can be done with:
```
conda create --name softwipe_env
conda install softwipe -c angtft -c conda-forge -n softwipe_env
```
Then, before running SoftWipe, you need to activate the environment with:
```
conda activate softwipe_env
```
Close the environment again with:
```
conda deactivate
```

#### Basic usage
SoftWipe can be run as follows:
```
softwipe.py [-c | -C] [-M | -m | -l target [target ...]] [-e EXECUTEFILE] programdir
```
Where:

`-c` tells SoftWipe that your program is C, and `-C` tells SoftWipe that you program is C++.

`-M` tells SoftWipe to build your program using CMake, `-m` using make, and `-l` using clang. The `-l` option takes as arguments the files to compile.

`-e` specifies the path to an "execute file" which contains a command line that executes your program.

`programdir` specifies the root directory of your target program.

Example command line for a CMake-based C++ program:
```
softwipe.py -CM path/to/program -e path/to/executefile
```

For more options and further information, run `softwipe.py --help`.

#### Docker usage

Docker enables an awesome way to use a out-of-the-box installation by calling 

```
docker run -it --rm -u <USER_ID>:<GROUP_ID> -w /work -v $PWD:/work softwipe/softwipe softwipe.py <SOFTWIPE_ARGS>
```

where `USER_ID`/`GROUP_ID` should be the owner of the host directory to have write permissions within the docker container.
The same image can also be used for continuous integration, shown here for the example of a Jenkins pipeline:

```
stage('Softwipe') {
  agent {
    docker {
      image 'softwipe/softwipe:0.1'
    }
  }
  steps {
    sh 'softwipe.py -CM -e run_softwipe.sh . 2>&1 |tee softwipe_general.txt'
  }
}
