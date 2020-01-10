"""
Functions related to the automatic installation of dependencies.
"""

import subprocess
import shutil
import os
import sys
import platform
import inspect

import strings
import util
import compile_phase
import tools_info


def detect_user_os():
    """
    Detect the users OS.
    :return: The name of the OS.
    """
    system = platform.system()
    if system == 'Linux':
        distro = platform.linux_distribution()
        detected_os = distro[0]
    else:
        detected_os = system
    return detected_os


def get_package_install_command_for_os(user_os):
    command = None
    if user_os == strings.OS_MACOS:
        command = ['brew', 'install']
    elif user_os == strings.OS_DEBIAN or user_os == strings.OS_UBUNTU:
        command = ['apt-get', 'install']
    return command


def print_missing_tools(missing_tools):
    print(strings.FAILED_TO_FIND_TOOLS)
    for missing_tool in missing_tools:
        print('  ' + missing_tool.install_name, '(install via:', missing_tool.install_via.name.lower() + ')')

    print(strings.MAKE_SURE_TOOLS_ARE_INSTALLED)


def print_and_run_install_command(install_command):
    for c in install_command:
        print(c, end=' ')
    print()
    subprocess.run(install_command)
    print()


def handle_kwstyle_download():
    git_link = 'https://github.com/Kitware/KWStyle.git'
    git_clone_command = ['git', 'clone', git_link]
    softwipe_dir = util.get_softwipe_directory()

    subprocess.run(git_clone_command, cwd=softwipe_dir)

    kwstyle_dir = os.path.join(softwipe_dir, 'KWStyle')
    print('Building KWStyle...')
    compile_phase.compile_program_cmake(kwstyle_dir, 1, dont_check_for_warnings=True, compiler_flags="",
                                        excluded_paths=())  # The argument lines_of_code does not matter here
    print('Done!')
    print()

def handle_infer_download():
    #TODO: properly select newest version
    version =  '0.17.0'
    url = "https://github.com/facebook/infer/releases/download/v{}/infer-linux64-v{}.tar.xz".format(version, version)
    ps = subprocess.Popen(('curl', '-sSL', url), stdout=subprocess.PIPE)
    output = subprocess.Popen(('sudo', 'tar', "-C", "/opt", "-xJ"), stdin=ps.stdout)
    output.wait()
    ps = subprocess.Popen(("sudo", "ln", "-s", "/opt/infer-linux64-v{}/bin/infer".format(version), "/usr/local/bin/infer"))
    ps.wait()

def handle_tool_download(tool_name):
    """
    If a tool has to be downloaded and installed manually, this function calls the correct handler for the tool.
    :param tool_name: The name of the tool.
    """
    if tool_name == 'KWStyle':
        handle_kwstyle_download()
    elif tool_name == 'infer':
        handle_infer_download()


def handle_clang_tidy_installation(package_install_command):
    """
    Special treatment for clang-tidy. Homebrew includes clang-tidy in llvm, apt-get has a separate package for
    clang-tidy. Thus, when using apt-get, do the extra installation.
    """
    if package_install_command[0] == 'apt-get':
        clang_tidy_install_command = package_install_command[:]
        clang_tidy_install_command.append('clang-tidy')

        print_and_run_install_command(clang_tidy_install_command)


def auto_tool_install(missing_tools, package_install_command):
    pip_install_command = ['python3', '-m', 'pip', 'install']
    for tool in missing_tools:
        install_command = []
        if tool.install_via == tools_info.Via.PACKAGE_MANAGER:
            install_command = package_install_command[:]
        elif tool.install_via == tools_info.Via.PIP:
            install_command = pip_install_command[:]
        elif tool.install_via == tools_info.Via.DOWNLOAD:
            handle_tool_download(tool.install_name)
            continue

        install_command.append(tool.install_name)

        print_and_run_install_command(install_command)

        if tool.exe_name == 'clang-tidy':
            handle_clang_tidy_installation(package_install_command)


def auto_install_prompt(missing_tools, package_install_command):
    print('I can automatically install the missing tools for you! Shall I? (Y/n)')
    while True:
        user_in = input('>>> ')
        if user_in == 'Y' or user_in == 'Yes':
            auto_tool_install(missing_tools, package_install_command)
            sys.exit(0)
        elif user_in == 'n' or user_in == 'no':
            sys.exit(1)
        else:
            print('Please answer with "Y" (Yes) or "n" (no)!')


def check_if_all_required_tools_are_installed():
    """
    Check if clang etc. (all the tools used in the pipeline) are installed on the system and can be used. If
    something is missing, print a warning and exit.
    """
    tools = [tool for tool in inspect.getmembers(tools_info.TOOLS) if not tool[0].startswith('_')]
    missing_tools = []
    for tool in tools:
        which_result = shutil.which(tool[1].exe_name)
        if which_result is None:  # if the tool is not installed / not accessible
            missing_tools.append(tool[1])

    if missing_tools:
        print_missing_tools(missing_tools)

        user_os = detect_user_os()
        package_install_command = get_package_install_command_for_os(user_os)
        if package_install_command is None:
            sys.exit(1)

        auto_install_prompt(missing_tools, package_install_command)
