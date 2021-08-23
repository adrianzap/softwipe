"""
This module contains all information concerning the tools that are used by softwipe.
"""

import collections
import enum
import os
import re
import subprocess

import scoring
import util
import strings
import compile_phase
import classifications
import output_classes
from tools_info import TOOLS

Tool = collections.namedtuple('Tool', ['exe_name', 'install_name', 'install_via'])
VIA = enum.Enum('VIA', 'PACKAGE_MANAGER PIP DOWNLOAD')


class AnalysisTool:
    def __init__(self):
        pass

    @staticmethod
    def run(data, skip_on_failure=False):
        """
        Executes the analysis tool and returns a score.
        :param data: dictionary containing all relevant data (such as file paths and lines of code)
        :param skip_on_failure: automatically skip the tool on error or raise exceptions
        :return: list of scores, textual score description (for console output), True - if analysis was successful
        """
        return [], "", False

    @staticmethod
    def name():
        return ""


class ClangTool(AnalysisTool):
    @staticmethod
    def run(data, skip_on_failure=False):
        pass

    @staticmethod
    def name():
        return "clang"


class CompileTool(AnalysisTool):
    # TODO: put compilation into classes (?)
    @staticmethod
    def run(data, skip_on_failure=False, compiler_flags=strings.COMPILER_WARNING_FLAGS):
        program_dir_abs = data["program_dir_abs"]
        args = data["args"]
        lines_of_code = data["lines_of_code"]
        excluded_paths = data["excluded_paths"]
        cpp = data["use_cpp"]
        """
        Run the automatic compilation of the target project.
        :param args: The "args" Namespace as returned from parse_arguments().
        :param lines_of_code: The lines of pure code count.
        :param cpp: Whether C++ is used or not. True if C++, False if C.
        :param compiler_flags: The flags to be used for compilation. Typically, these should be strings.COMPILE_FLAGS
            or, if no_execution, strings.COMPILER_WARNING_FLAGS.
        :param excluded_paths: A tuple containing the paths to be excluded.
        :return: The compiler score.
        """
        command_file = args.commandfile

        if args.make:
            if command_file:
                score = compile_phase.compile_program_make(program_dir_abs, lines_of_code, compiler_flags,
                                                           excluded_paths,
                                                           make_command_file=command_file[0])
            else:
                score = compile_phase.compile_program_make(program_dir_abs, lines_of_code, compiler_flags,
                                                           excluded_paths)
        elif args.clang:
            score = compile_phase.compile_program_clang(program_dir_abs, args.clang, lines_of_code, compiler_flags,
                                                        excluded_paths, cpp)
        else:
            if command_file:
                score = compile_phase.compile_program_cmake(program_dir_abs, lines_of_code, compiler_flags,
                                                            excluded_paths,
                                                            make_command_file=command_file[0])
            else:
                score = compile_phase.compile_program_cmake(program_dir_abs, lines_of_code, compiler_flags,
                                                            excluded_paths)

        return score

    @staticmethod
    def name():
        return "Compiler"


class AssertionTool(AnalysisTool):
    @staticmethod
    def is_assert(line, custom_asserts=None):
        """
        Check whether a line of code contains an assertion. Finds both C assert() calls and C++ static_assert().
        :return: True if there is an assertion, else False.
        """
        # This regex should match all ways in which assertions could occur.
        # It spits out false positives for ultra specific cases: when someone literally puts "assert(" in a string or
        # the mid of a block comment. This is fine though.
        # Breakdown of the regex: The first two negative lookaheads "(?! )" exclude commented assertions. Then,
        # match assert( and static_assert( while allowing for whitespace or code (e.g. ";" or "}") before the call.
        # If there are any custom asserts, add them to "custom". The regex will look for (assert|custom_assert).
        custom = r''
        if custom_asserts:
            for custom_assert in custom_asserts:
                custom += '|' + custom_assert

        regex = r'(?!^.*\/\/.*(assert' + custom + r')\s*\()(?!^.*\/\*.*(assert' + custom + \
                r')\s*\()^.*(\W|^)((static_)?assert' + custom + r')\s*\('
        return re.match(regex, line)

    @staticmethod
    def run(data, skip_on_failure=False):
        source_files = data["source_files"]
        lines_of_code = data["lines_of_code"]
        custom_asserts = data["custom_asserts"]

        assert_count = 0

        for path in source_files:
            file = open(path, 'r', encoding='latin-1')

            file_lines = file.readlines()
            for line in file_lines:
                if AssertionTool.is_assert(line, custom_asserts):
                    assert_count += 1
            file.close()

        assertion_rate = assert_count / lines_of_code

        detailled_result_string = strings.RESULT_ASSERTION_RATE_DETAILED.format(count=assert_count, loc=lines_of_code,
                                                                                rate=assertion_rate,
                                                                                percentage=100 * assertion_rate)

        util.write_into_file_string(strings.RESULTS_FILENAME_ASSERTION_CHECK, detailled_result_string)

        score = scoring.calculate_assertion_score_absolute(assertion_rate)

        log = strings.RUN_ASSERTION_CHECK_HEADER + "\n"
        log += strings.RESULT_ASSERTION_RATE.format(assertion_rate, assert_count, lines_of_code) + "\n"
        log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_ASSERTION_CHECK) + "\n"
        log += scoring.get_score_string(score, 'Assertion') + "\n"

        return [score], log, True

    @staticmethod
    def name():
        return "assertions"


class ClangTidyTool(AnalysisTool):
    @staticmethod
    def get_warning_lines(output):
        """
        Reads output log of clang-tidy and returns warning lines.
        :param output: clang-tidy output
        :return: warning lines
        """
        warning_lines = []

        output_lines = output.split('\n')
        do_add_warnings = False
        for line in output_lines:
            if util.clang_tidy_output_line_is_header(line):  # "n warnings generated."
                do_add_warnings = True

            if do_add_warnings:
                warning_lines.append(line)

            if util.clang_tidy_output_line_is_trailer(line):  # "Suppressed m warnings."
                do_add_warnings = False

        return warning_lines

    @staticmethod
    def get_weighted_warning_count(warning_lines):
        """
        Counts and weights clang-tidy warnings according to softwipe's warning classifications. The warnings softwipe
        considers more dangerous have a higher weight than the less dangerous ones.
        :param warning_lines: filtered clang-tidy warning lines
        :return: weighted warning count
        """
        warning_count = 0

        for line in warning_lines:
            if compile_phase.line_is_warning_line(line):
                warning_name = line.split()[-1][1:-1]
                warning_category = warning_name.split('-')[0]

                warning_level = 1
                if warning_category in classifications.CLANG_TIDY_WARNINGS:
                    warning_level = classifications.CLANG_TIDY_WARNINGS[warning_category]

                warning_count += warning_level

        return warning_count

    @staticmethod
    def beatify_warning_lines(warning_lines):
        """
        Removes the "n warnings generated" headers and "Suppressed m warnings" trailer for a more beautiful output
        :param warning_lines: The clang tidy warning lines as output by
        get_clang_tidy_warning_lines_from_clang_tidy_output(), which contain the ugly headers and trailer.
        :return: The warning lines with the headers and trailer removed.
        """
        beautified_lines = []
        for line in warning_lines:
            if not (util.clang_tidy_output_line_is_header(line) or util.clang_tidy_output_line_is_trailer(line)):
                beautified_lines.append(line)

        return beautified_lines

    @staticmethod
    def run(data, skip_on_failure=False, num_tries=5):
        program_dir_abs = data["program_dir_abs"]
        source_files = data["source_files"]
        lines_of_code = data["lines_of_code"]
        cpp = data["use_cpp"]
        """
        Runs clang-tidy.
        :param program_dir_abs: The absolute path to the root directory of the target program.
        :param source_files: The lst of source files to analyze.
        :param lines_of_code: The lines of pure code count.
        :param cpp: Whether C++ is used or not. True if C++, false if C.
        :param num_tries: The amount of times clang-tidy should be rerun if it runs into internal problems
        :return: 1. The clang-tidy score.
                 2. output log
                 3. boolean success
        """
        clang_tidy_call = [TOOLS.CLANG_TIDY.exe_name]
        clang_tidy_call.extend(source_files)

        # Create checks lst
        clang_tidy_checks = strings.CLANG_TIDY_CHECKS_CPP if cpp else strings.CLANG_TIDY_CHECKS_C
        clang_tidy_call.append('-checks=' + clang_tidy_checks)
        clang_tidy_call.extend(['-p', program_dir_abs])

        try:
            output = subprocess.check_output(clang_tidy_call, universal_newlines=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = error.output

            if num_tries < 0:  # make clang-tidy return a failure status if it has no tries left
                return [0], "", False

            if error.returncode == -11:  # clang-tidy seems to run into segfaults sometimes, so rerun it if that happens
                return ClangTidyTool.run(data, num_tries=num_tries-1)
            # clang-tidy can exit with exit code 1 if there is no compilation database, which might be the case when
            # compiling with just clang. Thus, ignore the exception here.
        except Exception:  # catch the rest and exclude the analysis tool from the score
            if not skip_on_failure:
                raise
            return [0], "", False

        warning_lines = ClangTidyTool.get_warning_lines(output)
        weighted_warning_count = ClangTidyTool.get_weighted_warning_count(warning_lines)
        warning_rate = weighted_warning_count / lines_of_code

        beautified_warning_lines = ClangTidyTool.beatify_warning_lines(warning_lines)
        util.write_into_file_list(strings.RESULTS_FILENAME_CLANG_TIDY, beautified_warning_lines)

        score = scoring.calculate_clang_tidy_score_absolute(warning_rate)

        log = strings.RUN_CLANG_TIDY_HEADER + "\n"
        log += strings.RESULT_WEIGHTED_CLANG_TIDY_WARNING_RATE.format(warning_rate, weighted_warning_count,
                                                                      lines_of_code) + "\n"
        log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_CLANG_TIDY) + "\n"
        log += scoring.get_score_string(score, 'Clang-tidy') + "\n"

        return [score], log, True

    @staticmethod
    def name():
        return "Clang-Tidy"


class LizardTool(AnalysisTool):
    @staticmethod
    def filter_output(output):
        """
        Filters the important (for us) information out of Lizard general output.
        :param output: Lizard output
        :return: filtered information string
        """
        output_lines = output.split('\n')

        # Get total number of functions and standard lizard information (CCN & warning count)
        function_count = 0
        currently_counting_functions = False
        function_counting_finished = False
        summary_line = None
        for i, output_line in enumerate(output_lines):
            # Function counting
            if currently_counting_functions:
                if output_line.endswith('analyzed.'):  # Stop counting at the right point
                    currently_counting_functions = False
                    function_counting_finished = True
                else:
                    function_count += 1
            if output_line.startswith('--') and not function_counting_finished:  # Start counting after this
                currently_counting_functions = True

            # Getting the information
            if output_line.startswith('Total nloc'):
                summary_line = output_lines[i + 2]  # This line contains the information we need
        split_summary_line = summary_line.split()

        avg_ccn = float(split_summary_line[2])
        warning_cnt = int(split_summary_line[5])

        # Get -Eduplicate information
        unique_rate_line = output_lines[-2]

        percentage_string = unique_rate_line.split()[-1]  # Get the percentage
        unique_rate = float(percentage_string[:-1]) / 100

        lizard_output = output_classes.LizardOutput(avg_ccn, warning_cnt, unique_rate, function_count)
        return lizard_output

    @staticmethod
    def run(data, skip_on_failure=False):
        source_files = data["source_files"]
        """
        Runs Lizard.
        :param source_files: The lst of source files to analyze.
        :return: The cyclomatic complexity score, warning score, and unique score
        """
        # NOTE Although lizard can be imported as a python module it is actually easier to parse its output
        # (for now at least - this might of course change). This is because the module is not well documented so it's
        # hard to find out how exactly one can get _all_ information using it. Plus, this way we can check if it is
        # installed using shutil.which --> consistent with how we check for the other tools.

        lizard_call = [TOOLS.LIZARD.exe_name, '-Eduplicate', '-l', 'cpp']
        lizard_call.extend(source_files)

        try:
            output = subprocess.check_output(lizard_call, universal_newlines=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:  # If warnings are generated, Lizard exits with exit code 1
            # Basically, this catches the exception and ignores it such that this tool doesn't crash
            # while still keeping the output of the command
            output = error.output
        except Exception:  # catch the rest and exclude the analysis tool from the score
            if not skip_on_failure:
                raise
            return [0, 0, 0], "", False

        lizard_output = LizardTool.filter_output(output)
        cyclomatic_complexity_score, warning_score, unique_score, temp = \
            lizard_output.get_information()
        util.write_into_file_string(strings.RESULTS_FILENAME_LIZARD, output)

        log = strings.RUN_LIZARD_HEADER + "\n"
        log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_LIZARD) + "\n"
        log += temp

        return [cyclomatic_complexity_score, warning_score, unique_score], log, True

    @staticmethod
    def name():
        return "Lizard"


class CppcheckTool(AnalysisTool):
    @staticmethod
    def get_warning_lines(output):
        warning_lines = []

        output_lines = output.split('\n')
        for line in output_lines:
            # if line.startswith('['):  # Informative lines start with "[/path/to/file.c] (error/warning) ..."
            # changed with newer version of cppcheck
            if '[' in line:
                warning_lines.append(line)

        return warning_lines

    @staticmethod
    def run(data, skip_on_failure=False):
        source_files = data["source_files"]
        lines_of_code = data["lines_of_code"]
        cpp = data["use_cpp"]

        language = 'c++' if cpp else 'c'
        # TODO: find out the purpose of the --template=cppcheck1' which broke the output
        cppcheck_call = [TOOLS.CPPCHECK.exe_name, '--enable=all', '--force', '--language=' + language, "-v"]

        output = ""
        chunk_size = 1000  # should fix that "OSError: [Errno 7] Argument lst too long: 'cppcheck'" thing

        try:
            argument_chunks = util.split_in_chunks(source_files, chunk_size)
            for chunk in argument_chunks:
                temp_call = cppcheck_call   # TODO: check this again
                temp_call.extend(chunk)
                output += subprocess.check_output(cppcheck_call, universal_newlines=True,
                                                  stderr=subprocess.STDOUT, encoding='utf-8', errors='ignore') + "\n"
            warning_lines = CppcheckTool.get_warning_lines(output)
            cppcheck_output = output_classes.CppcheckOutput(warning_lines)
        except subprocess.CalledProcessError as error:
            print("cppcheck failed!")
            print(strings.COMPILATION_CRASHED.format(error.returncode, error.output))
            if not skip_on_failure:
                raise
            return [0], "", False
        except Exception:  # catch the rest and exclude the analysis tool from the score
            if not skip_on_failure:
                raise
            return [0], "", False

        weighted_cppcheck_rate, temp = cppcheck_output.get_information(lines_of_code)
        util.write_into_file_list(strings.RESULTS_FILENAME_CPPCHECK, warning_lines)

        score = scoring.calculate_cppcheck_score_absolute(weighted_cppcheck_rate)

        log = strings.RUN_CPPCHECK_HEADER + "\n"
        log += temp
        log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_CPPCHECK) + "\n"
        log += scoring.get_score_string(score, 'Cppcheck') + "\n"

        return [score], log, True

    @staticmethod
    def name():
        return "Cppcheck"


class KWStyleTool(AnalysisTool):
    @staticmethod
    def get_warning_count(output):
        """
        Counts warnings in the kwstyle output.
        :param output: kwstyle output log
        :return: number of found warnings
        """
        warning_count = 0

        output_lines = output.split('\n')
        for line in output_lines:
            if line.startswith('Error'):
                warning_count += 1

        return warning_count

    @staticmethod
    def run(data, skip_on_failure=False):
        source_files = data["source_files"]
        lines_of_code = data["lines_of_code"]

        softwipe_directory = os.path.dirname(os.path.realpath(__file__))
        kwstyle_xml = os.path.join(softwipe_directory, 'KWStyle.xml')
        kwstyle_call = [TOOLS.KWSTYLE.exe_name, '-v', '-xml', kwstyle_xml]

        output = ''
        # KWStyle only works properly when specifying just one single input file. Thus, iterate and call KWStyle again
        # for each source file, each time appending to the result output.
        for source_file in source_files:
            cur_kwstyle_call = kwstyle_call[::]
            cur_kwstyle_call.append(source_file)
            try:
                output += subprocess.check_output(cur_kwstyle_call, universal_newlines=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as error:
                # Same as with the lizard call. KWStyle exits with status 1 by default.
                # So catch that, ignore the exception, and keep the output of the command
                output += error.output
            except Exception:  # catch the rest and exclude the analysis tool from the score
                if not skip_on_failure:
                    raise
                return [0], "", False

        warning_count = KWStyleTool.get_warning_count(output)
        warning_rate = warning_count / lines_of_code

        util.write_into_file_string(strings.RESULTS_FILENAME_KWSTYLE, output)

        score = scoring.calculate_kwstyle_score_absolute(warning_rate)

        log = strings.RUN_KWSTYLE_HEADER + "\n"
        log += strings.RESULT_KWSTYLE_WARNING_RATE.format(warning_rate, warning_count, lines_of_code) + "\n"
        log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_KWSTYLE) + "\n"
        log += scoring.get_score_string(score, 'KWStyle') + "\n"

        return [score], log, True

    @staticmethod
    def name():
        return "KWStyle"


class InferTool(AnalysisTool):
    @staticmethod
    def get_warnings_from_output(infer_out_path):
        """
        Reads Infer report file from 'infer_out_path', counts and weights warnings and returns
        the content of the report file, summarized warnings, and weighted number of warnings.
        :param infer_out_path: path to infer report file
        :return: 1. report lines
                 2. summarized warnings (multi-line string)
                 3. weighted number of warnings
        """
        warning_num = 0
        warnings = ""
        record = False
        file_out = ""

        with open(infer_out_path) as file:
            for line in file:
                file_out += line
                line = line.rstrip()
                if not line:
                    continue
                if record:
                    warnings += line + "\n"
                    line = line.replace(" ", "").split(":")
                    category = line[0]
                    if category in classifications.INFER_WARNINGS:
                        factor = classifications.INFER_WARNINGS[category]
                    else:
                        factor = 1
                    if category != "":
                        warning_num += factor * int(line[-1])
                if "Summary of the reports" in line:
                    record = True

        return file_out, warnings, warning_num

    @staticmethod
    def prepare_exclude_arguments(program_dir_abs, excluded_paths):
        """
        Prepares the arguments to add to the 'infer capture' call to exclude certain files from the analysis.
        :param program_dir_abs: The absolute path to the root directory of the target program.
        :param excluded_paths: A lst containing absolute paths to files to be excluded.
        :return: arguments used to exclude files for the 'infer capture' call
        """
        exclude_command = []
        for path in excluded_paths:
            if program_dir_abs[-1] != '/':
                program_dir_abs += '/'
            path = path.replace(program_dir_abs, "")
            exclude_command.extend(["--skip-analysis-in-path", path])
        return exclude_command

    @staticmethod
    def compile_with_cmake(program_dir_abs, excluded_paths):
        """
        Compile the program with infer using cmake to allow infer to analyze it later.
        :param program_dir_abs: The absolute path to the root directory of the target program.
        :param excluded_paths: A lst containing files to be excluded.
        :return: True if the compilation was successful
                 False if the compilation was not successful
        """
        build_path = util.create_build_directory(program_dir_abs, build_dir_name="infer_build")
        util.clear_directory(build_path)

        infer_call_compile = ["infer", "compile", "--", "cmake", ".."]
        infer_call_capture = ["infer", "capture"]
        infer_call_capture.extend(InferTool.prepare_exclude_arguments(program_dir_abs, excluded_paths))
        infer_call_capture.extend(["--", "make"])

        try:
            subprocess.check_output(infer_call_compile, cwd=build_path, universal_newlines=True,
                                    stderr=subprocess.STDOUT)
            subprocess.check_output(infer_call_capture, cwd=build_path, universal_newlines=True,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            util.write_into_file_string(strings.ERROR_FILENAME_INFER_COMPILATION,
                                        strings.INFER_COMPILATION_CRASHED.format(e.returncode, e.output))
            print(strings.INFER_COMPILATION_CRASHED.format(e.returncode, strings.ERROR_LOG_WRITTEN_INTO.format(
                strings.ERROR_FILENAME_INFER_COMPILATION)))
            print()
            return False
        return True

    @staticmethod
    def compile_with_make(program_dir_abs, excluded_paths):
        """
        Compile the program with infer using make to allow infer to analyze it later.
        :param program_dir_abs: The absolute path to the root directory of the target program.
        :param excluded_paths: A lst containing files to be excluded.
        :return: True if the compilation was successful
                 False if the compilation was not successful
        """
        exclude_args = InferTool.prepare_exclude_arguments(program_dir_abs, excluded_paths)
        infer_call = [TOOLS.INFER.exe_name, "capture"]
        infer_call.extend(exclude_args)
        infer_call.extend(["--", "make"])
        make_clean_call = ["make", "clean"]

        try:
            subprocess.check_output(make_clean_call, cwd=program_dir_abs, universal_newlines=True,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:  # not all makefiles have a clean option, pass if it doesn't exist
            pass

        try:
            subprocess.check_output(infer_call, cwd=program_dir_abs, universal_newlines=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            util.write_into_file_string(strings.ERROR_FILENAME_INFER_COMPILATION,
                                        strings.INFER_COMPILATION_CRASHED.format(e.returncode, e.output))
            print(strings.INFER_COMPILATION_CRASHED.format(e.returncode, strings.ERROR_LOG_WRITTEN_INTO.format(
                strings.ERROR_FILENAME_INFER_COMPILATION)))
            print()
            return False
        return True

    @staticmethod
    def run(data, skip_on_failure=False):
        program_dir_abs = data["program_dir_abs"]
        lines_of_code = data["lines_of_code"]
        use_cmake = data["use_cmake"]
        use_make = data["use_make"]
        excluded_paths = data["excluded_paths"]
        compilation_status = False

        if use_cmake:
            program_dir_abs += "/" + strings.INFER_BUILD_DIR_NAME
            compilation_status = InferTool.compile_with_cmake(program_dir_abs, excluded_paths)
        elif use_make:
            compilation_status = InferTool.compile_with_make(program_dir_abs, excluded_paths)

        if not compilation_status:
            return [0], "", False

        # TODO: maybe fix the error handling differently (not by the --keep-going flag)
        infer_analyze = [TOOLS.INFER.exe_name, "analyze", "--keep-going"]

        try:
            subprocess.check_output(infer_analyze, cwd=program_dir_abs, universal_newlines=True,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            print(strings.COMPILATION_CRASHED.format(error.returncode, error.output))
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(error).__name__, error.args)
            print(message)
            if not skip_on_failure:
                raise
            return [0], "", False
        except Exception:  # catch the rest and exclude the analysis tool from the score
            if not skip_on_failure:
                raise
            return [0], "", False

        infer_out_path = util.find_file(program_dir_abs, strings.INFER_OUTPUT_FILE_NAME,
                                        directory=strings.INFER_OUTPUT_DIR_NAME)
        if infer_out_path == "":
            return [0], "Could not find {}".format(strings.INFER_OUTPUT_FILE_NAME), False

        file_out, warnings, warning_num = InferTool.get_warnings_from_output(infer_out_path)
        util.write_into_file_string(strings.RESULTS_FILENAME_INFER, file_out)

        infer_warning_rate = warning_num / lines_of_code
        score = scoring.calculate_infer_score_absolute(infer_warning_rate)

        log = strings.RUN_INFER_ANALYSIS_HEADER + "\n"
        log += warnings + "\n"
        # TODO: make and print filename to user
        log += "Weighted Infer warning rate: {} ({}/{})".format(warning_num / lines_of_code, warning_num,
                                                                lines_of_code) + "\n"
        log += scoring.get_score_string(score, 'Infer') + "\n"

        return [score], log, True

    @staticmethod
    def name():
        return "Infer"


class ValgrindTool(AnalysisTool):
    @staticmethod
    def get_weighted_warning_count(output):
        wcount = 0
        for line in output:
            for w in classifications.VALGRIND_WARNINGS:
                if w in line:
                    wcount += classifications.VALGRIND_WARNINGS[w]
        return wcount

    @staticmethod
    def get_warning_log(output):
        record = False
        log = ""
        for line in output.split("\n"):
            if "HEAP SUMMARY" in line:
                record = True
            if "Rerun" in line:
                record = False
            if record:
                log += re.sub('==[^=]+==', '', line) + "\n"
        return log

    @staticmethod
    def run(data, skip_on_failure=False):
        program_dir_abs = data["program_dir_abs"] + "/softwipe_build/" if data["use_cmake"] else data["program_dir_abs"]
        executefile = data["executefile"][0]
        lines_of_code = data["lines_of_code"]
        CompileTool.run(data)

        print(executefile)
        print("-------- RERUNNING COMPILATION FOR VALGRIND --------")
        print(strings.RUN_EXECUTION_WITH_SANITIZERS_HEADER)

        command = ["valgrind", "--error-exitcode=123"]
        output = ""

        print(program_dir_abs)

        if executefile and os.path.isfile(executefile):
            file = open(executefile, 'r')
            lines = file.readlines()
            file.close()

            command_line = os.path.join(program_dir_abs, lines[0])
            command.extend(command_line.split())

        # Execute and get stderr, which contains the output of the sanitizers
        print(command)

        try:
            output = subprocess.check_output(command, cwd=program_dir_abs, universal_newlines=True,
                                             stderr=subprocess.STDOUT)
        except FileNotFoundError as e1:
            print(e1)
            print(strings.EXECUTION_FILE_NOT_FOUND.format(command[1]))
            return [], "", False
        except subprocess.CalledProcessError as error:
            if error.returncode == 123:
                pass
            else:
                print(error.output)
                raise

        weighted_warnings = ValgrindTool.get_weighted_warning_count(output)
        warning_rate = weighted_warnings / lines_of_code
        warning_log = ValgrindTool.get_warning_log(output)
        score = scoring.calculate_valgrind_score_absolute(warning_rate)

        util.write_into_file_string(strings.RESULTS_FILENAME_VALGRIND, output)

        log = strings.RUN_VALGRIND_ANALYSIS_HEADER + "\n"
        log += warning_log + "\n"
        # TODO: make and print filename to user
        log += "Weighted Valgrind warning rate: {} ({}/{})".format(weighted_warnings / lines_of_code, weighted_warnings,
                                                                   lines_of_code) + "\n"
        log += scoring.get_score_string(score, ValgrindTool.name()) + "\n"
        log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_VALGRIND)

        return [score], log, True

    @staticmethod
    def name():
        return "Valgrind"


class TestCountTool(AnalysisTool):
    @staticmethod
    def run(data, skip_on_failure=False):
        loc = data["lines_of_code"]
        source_files = data["source_files"]

        source_files_wo_tests = [x for x in source_files if not util.is_testfile(x)]
        loc_wo_tests = util.count_lines_of_code(source_files_wo_tests)

        rate = (loc - loc_wo_tests) / loc
        score = scoring.calculate_testcount_score_absolute(rate)

        log = " --- TEST COUNT --- \n"
        log += strings.LINES_OF_PURE_CODE_ARE.format(loc) + "\n"
        log += "Amount of unit test LOC compared to overall LOC: {} ({}/{})\n".format(rate, (loc - loc_wo_tests), loc)
        log += scoring.get_score_string(score, TestCountTool.name()) + "\n"

        return [score], log, True

    @staticmethod
    def name():
        return "TestCount"
