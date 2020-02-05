"""
This module contains softwipes classifications of various warnings into severity levels 1 - 3:
1 = could be fixed (style issues)
2 = should be fixed (might cause problems or bugs)
3 = must be fixed (dangerous or highly bugprone)
"""

COMPILER_WARNINGS = {
 '-Wabsolute-value': 3,
 '-Wbad-function-cast': 3,
 '-Wc11-extensions': 2,
 '-Wc99-extensions': 1,
 '-Wcast-align': 2,
 '-Wcast-qual': 1,
 '-Wchar-subscripts': 1,
 '-Wcomma': 2,
 '-Wcomment': 1,
 '-Wconditional-uninitialized': 3,
 '-Wconstant-conversion': 3,
 '-Wconversion': 3,
 '-Wcovered-switch-default': 1,
 '-Wdate-time': 1,
 '-Wdelete-non-virtual-dtor': 3,
 '-Wdeprecated': 1,
 '-Wdeprecated-declarations': 2,
 '-Wdeprecated-dynamic-exception-spec': 1,
 '-Wdeprecated-register': 1,
 '-Wdocumentation': 1,
 '-Wdocumentation-deprecated-sync': 1,
 '-Wdocumentation-unknown-command': 1,
 '-Wdouble-promotion': 2,
 '-Wempty-body': 2,
 '-Wexit-time-destructors': 1,
 '-Wexpansion-to-defined': 2,
 '-Wextra-semi': 1,
 '-Wfloat-conversion': 3,
 '-Wfloat-equal': 3,
 '-Wfor-loop-analysis': 2,
 '-Wformat': 2,
 '-Wformat-extra-args': 2,
 '-Wformat-nonliteral': 2,
 '-Wformat-security': 3,
 '-Wglobal-constructors': 1,
 '-Wgnu-binary-literal': 2,
 '-Wgnu-zero-variadic-macro-arguments': 1,
 '-Wheader-hygiene': 3,
 '-Wimplicit-fallthrough': 3,
 '-Wimplicit-int': 2,
 '-Wincompatible-library-redeclaration': 2,
 '-Winfinite-recursion': 3,
 '-Winvalid-source-encoding': 2,
 '-Wlanguage-extension-token': 2,
 '-Wliteral-conversion': 3,
 '-Wlogical-not-parentheses': 2,
 '-Wlogical-op-parentheses': 2,
 '-Wmacro-redefined': 2,
 '-Wmissing-declarations': 1,
 '-Wmissing-noreturn': 1,
 '-Wmissing-prototypes': 2,
 '-Wmissing-variable-declarations': 2,
 '-Wmultichar': 3,
 '-Wnested-anon-types': 2,
 '-Wnonnull': 2,
 '-Wnon-virtual-dtor': 3,
 '-Wnull-arithmetic': 3,
 '-Wnull-conversion': 3,
 '-Wold-style-cast': 1,
 '-Woverlength-strings': 3,
 '-Woverloaded-virtual': 1,
 '-Wparentheses': 2,
 '-Wparentheses-equality': 1,
 '-Wpedantic': 2,
 '-Wpointer-bool-conversion': 3,
 '-Wpointer-sign': 3,
 '-Wreorder': 1,
 '-Wreserved-id-macro': 2,
 '-Wreturn-type': 3,
 '-Wself-assign': 3,
 '-Wself-assign-field': 3,
 '-Wself-assign-overloaded': 3,
 '-Wself-move': 3,
 '-Wshadow': 2,
 '-Wshadow-field': 1,
 '-Wshadow-field-in-constructor': 1,
 '-Wshadow-field-in-constructor-modified': 1,
 '-Wshift-sign-overflow': 3,
 '-Wshorten-64-to-32': 3,
 '-Wsign-compare': 3,
 '-Wsign-conversion': 3,
 '-Wsometimes-uninitialized': 3,
 '-Wstatic-self-init': 3,
 '-Wstring-plus-int': 3,
 '-Wstrict-prototypes': 2,
 '-Wstring-compare': 3,
 '-Wstring-conversion': 3,
 '-Wswitch-bool': 2,
 '-Wswitch-enum': 2,
 '-Wtautological-constant-compare': 3,
 '-Wtautological-pointer-compare': 3,
 '-Wtautological-type-limit-compare': 3,
 '-Wtautological-unsigned-zero-compare': 3,
 '-Wundef': 3,
 '-Wundefined-func-template': 2,
 '-Wuninitialized': 3,
 '-Wunknown-pragmas': 1,
 '-Wunreachable-code': 1,
 '-Wunreachable-code-break': 2,
 '-Wunreachable-code-loop-increment': 2,
 '-Wunreachable-code-return': 2,
 '-Wunused-exception-parameter': 1,
 '-Wunused-function': 1,
 '-Wunused-macros': 1,
 '-Wunused-parameter': 2,
 '-Wunused-private-field': 2,
 '-Wunused-template': 1,
 '-Wunused-value': 2,
 '-Wunused-variable': 2,
 '-Wused-but-marked-unused': 1,
 '-Wvarargs': 1,
 '-Wvector-conversion': 3,
 '-Wvexing-parse': 2,
 '-Wvla': 2,
 '-Wvla-extension': 2,
 '-Wweak-vtables': 1,
 '-Wwritable-strings': 1,
 '-Wzero-as-null-pointer-constant': 2
}

CPPCHECK_WARNINGS = {
 'error': 3,
 'warning': 3,
 'style': 1,
 'performance': 1,
 'portability': 3,
 'information': 0
}

CLANG_TIDY_WARNINGS = {
 'bugprone': 2,
 'clang': 2,  # Actually clang-analyzer (Clang Static Analyzer warnings) but we don't want a - in the category name
 # since get_weighted_clang_tidy_warning_count_from_clang_tidy_warning_lines() wouldn't work with it
 'misc': 1,
 'modernize': 1,
 'mpi': 2,
 'performance': 1,
 'readability': 1,
 'boost': 1,
 'cppcoreguidelines': 1
}

INFER_WARNINGS = {   #TODO: fill this up a bit
 'DEADLOCK': 2,
 'DEAD_STORE': 1,
 'EMPTY_VECTOR_ACCESS': 2,
 'IMMUTABLE_CAST': 1,
 'NULL_DEREFERENCE': 1,
 'MEMORY_LEAK': 3,
 'RESOURCE_LEAK': 2,
 'UNINITIALIZED_VALUE': 1
}
