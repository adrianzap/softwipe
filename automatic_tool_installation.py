"""
Functions related to the automatic installation of dependencies.
"""

import inspect
import os
import platform
import shutil
import subprocess
import sys

import compile_phase
import strings
import tools_info
import util


def detect_user_os():
    """
    Detect the users OS.
    :return: The name of the OS.
    """
    system = platform.system()
    if system == 'Linux':
        import distro
        detected_distro = distro.linux_distribution(full_distribution_name=False)
        detected_os = detected_distro[0]
    else:
        detected_os = system
    return detected_os


def get_package_install_command_for_os(user_os):
    command = None
    if user_os == strings.OS_MACOS:
        command = ['brew', 'install']
    elif user_os in (strings.OS_DEBIAN, strings.OS_UBUNTU):
        command = ['apt-get', 'install']
    return command


def print_missing_tools(missing_tools):
    print(strings.FAILED_TO_FIND_TOOLS)
    for missing_tool in missing_tools:
        print('  ' + missing_tool.install_name, '(install via:', missing_tool.install_via.name.lower() + ')')

    print(strings.MAKE_SURE_TOOLS_ARE_INSTALLED)


def print_and_run_install_command(install_command):
    for argument in install_command:
        print(argument, end=' ')
    print()
    subprocess.run(install_command)
    print()


def handle_libtinfo_download():
    print('Infer requires libtinfo5 and opam packages to run. Should I try to install these now? (Y/n)')
    while True:
        user_in = input('>>> ')
        if user_in in ('Y', 'Yes'):
            install_command = ["sudo", "apt", "install", "libtinfo5", "opam"]
            subprocess.run(install_command)
            print('Done!')
            # print()
            # sys.exit(0)
            return
        elif user_in in ('n', 'no'):
            return
            # sys.exit(1)
        else:
            print('Please answer with "Y" (Yes) or "n" (no)!')


def install_apt_package_if_needed(package_name):
    command = ["dpkg", "-s", package_name]
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        if error.returncode == 1:
            handle_libtinfo_download()


def handle_kwstyle_download():
    softwipe_dir = util.get_softwipe_directory()
    kwstyle_dir = os.path.join(softwipe_dir, 'KWStyle')
    try:
        print("Downloading KWStyle...")
        git_link = 'https://github.com/Kitware/KWStyle.git'
        git_clone_command = ['git', 'clone', git_link]

        subprocess.run(git_clone_command, cwd=softwipe_dir)
        
        print('Building KWStyle...')
        compile_phase.compile_program_cmake(kwstyle_dir, 1, dont_check_for_warnings=True, compiler_flags="",
                                            excluded_paths=())  # The argument lines_of_code does not matter here
        print('Done!')
        print()
    except Exception as e:
        print(e)
        shutil.rmtree(kwstyle_dir)


def handle_lizard_download():
    softwipe_dir = util.get_softwipe_directory()
    version = '1.17.7'
    url = "https://github.com/terryyin/lizard/archive/{v}.tar.gz".format(v=version)
    print("Downloading lizard...")
    process = subprocess.Popen(('curl', '-sSL', url), cwd=softwipe_dir, stdout=subprocess.PIPE)
    output = subprocess.Popen(('tar', "-C", softwipe_dir, "-xz"), stdin=process.stdout)
    output.wait()
    print("Done!\n")


def handle_infer_download():
    print("Downloading Infer... (this might take a while)")
    softwipe_dir = util.get_softwipe_directory()
    # TODO: properly select newest version
    version = '0.17.0'
    url = "https://github.com/facebook/infer/releases/download/v{v}/infer-linux64-v{v}.tar.xz".format(v=version)
    process = subprocess.Popen(('curl', '-sSL', url), stdout=subprocess.PIPE)
    output = subprocess.Popen(('tar', "-C", softwipe_dir, "-xJ"), stdin=process.stdout)
    output.wait()


def handle_tool_download(tool_name):
    """
    If a tool has to be downloaded and installed manually, this function calls the correct handler for the tool.
    :param tool_name: The name of the tool.
    """
    if tool_name == 'KWStyle':
        handle_kwstyle_download()
    elif tool_name == 'infer':
        handle_infer_download()
    elif tool_name == 'lizard.py':
        handle_lizard_download()


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
        if tool.install_via == tools_info.VIA.PACKAGE_MANAGER:
            install_command = package_install_command[:]
        elif tool.install_via == tools_info.VIA.PIP:
            install_command = pip_install_command[:]
        elif tool.install_via == tools_info.VIA.DOWNLOAD:
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
        if user_in in ('Y', 'Yes'):
            auto_tool_install(missing_tools, package_install_command)
            sys.exit(0)
        elif user_in in ('n', 'no'):
            sys.exit(1)
        else:
            print('Please answer with "Y" (Yes) or "n" (no)!')


def check_if_all_required_tools_are_installed():
    """
    Check if clang etc. (all the tools used in the pipeline) are installed on the system and can be used. If
    something is missing, print a warning and exit.
    """
    tools = [tool for tool in inspect.getmembers(tools_info.TOOLS) if not tool[0].startswith('_')
             and 'infer' not in tool[1].exe_name
             and 'lizard' not in tool[1].exe_name]  # and 'KWStyle' not in tool[1].exe_name]
    missing_tools = []
    for tool in tools:
        which_result = shutil.which(tool[1].exe_name)
        if which_result is None:  # if the tool is not installed / not accessible
            missing_tools.append(tool[1])
            print("missing: {}".format(tool[1].exe_name))

    if missing_tools:
        print_missing_tools(missing_tools)

        user_os = detect_user_os()
        package_install_command = get_package_install_command_for_os(user_os)
        # if package_install_command is None:
        #    sys.exit(1)

        auto_install_prompt(missing_tools, package_install_command)
