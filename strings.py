COMPILER_WARNING_FLAGS = '-Weverything'
SET_CMAKE_CXX_FLAGS_COMPILER_WARNINGS = 'set(CMAKE_CXX_FLAGS "' + COMPILER_WARNING_FLAGS + ' ${CMAKE_CXX_FLAGS}")'
SET_CMAKE_C_FLAGS_COMPILER_WARNINGS = 'set(CMAKE_C_FLAGS "' + COMPILER_WARNING_FLAGS + ' ${CMAKE_C_FLAGS}")'


# These may be modified to contain a full path
CLANG = 'clang'
CLANGPP = 'clang++'
CMAKE = 'cmake'
MAKE = 'make'
COMPILEDB = 'compiledb'
CPPCHECK = 'cppcheck'
SPLINT = 'splint'
FLAWFINDER = 'flawfinder'
CLANG_TIDY = 'clang-tidy'
QMCALC = 'qmcalc'


_dashes = ' --- '
_running = 'Running: '
_header = _dashes + _running + '{}' + _dashes
RUN_COMPILER_HEADER = _header.format('COMPILER')
RUN_ASSERTION_CHECK_HEADER = _header.format('ASSERTION CHECK')
RUN_CPPCHECK_HEADER = _header.format('CPPCHECK')
RUN_SPLINT_HEADER = _header.format('SPLINT')
RUN_FLAWFINDER_HEADER = _header.format('FLAWFINDER')
RUN_CLANG_TIDY_HEADER = _header.format('CLANG-TIDY')
RUN_QMCALC_HEADER = _header.format('QMCALC')
RUN_CPD_HEADER = _header.format('PMD CPD')
