# Copyright (C) 2022 luckytyphlosion
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import platform
import time
import os
from runtime_error_with_exit_code import RuntimeErrorWithExitCode

if platform.system() == "Windows":
    import win32process
    import win32job

# Taken from https://stackoverflow.com/questions/1230669/subprocess-deleting-child-processes-in-windows/12942797#12942797

STILL_ACTIVE = 259

# From https://github.com/python/cpython/blob/3.10/Lib/subprocess.py#L529
# Licensed under Python license
# Technically accessible but undocumented so better to just copy the function
def list2cmdline(seq):
    """
    Translate a sequence of arguments into a command line
    string, using the same rules as the MS C runtime:
    1) Arguments are delimited by white space, which is either a
       space or a tab.
    2) A string surrounded by double quotation marks is
       interpreted as a single argument, regardless of white space
       contained within.  A quoted string can be embedded in an
       argument.
    3) A double quotation mark preceded by a backslash is
       interpreted as a literal double quotation mark.
    4) Backslashes are interpreted literally, unless they
       immediately precede a double quotation mark.
    5) If backslashes immediately precede a double quotation mark,
       every pair of backslashes is interpreted as a literal
       backslash.  If the number of backslashes is odd, the last
       backslash escapes the next double quotation mark as
       described in rule 3.
    """

    # See
    # http://msdn.microsoft.com/en-us/library/17w5ykft.aspx
    # or search http://msdn.microsoft.com for
    # "Parsing C++ Command-Line Arguments"
    result = []
    needquote = False
    for arg in map(os.fsdecode, seq):
        bs_buf = []

        # Add a space to separate this argument from the others
        if result:
            result.append(' ')

        needquote = (" " in arg) or ("\t" in arg) or not arg
        if needquote:
            result.append('"')

        for c in arg:
            if c == '\\':
                # Don't know if we need to double yet.
                bs_buf.append(c)
            elif c == '"':
                # Double backslashes.
                result.append('\\' * len(bs_buf)*2)
                bs_buf = []
                result.append('\\"')
            else:
                # Normal char
                if bs_buf:
                    result.extend(bs_buf)
                    bs_buf = []
                result.append(c)

        # Add remaining backslashes, if any.
        if bs_buf:
            result.extend(bs_buf)

        if needquote:
            result.extend(bs_buf)
            result.append('"')

    return ''.join(result)

def run_subprocess_as_job(cmd_and_args):
    if platform.system() != "Windows":
        raise RuntimeError(f"TODO: unsupported operating system for run_subprocess_as_job ({platform.system()})")

    cmd_as_str = list2cmdline(cmd_and_args)
    print(f"cmd_as_str: {cmd_as_str}")

    startup = win32process.STARTUPINFO()
    (hProcess, hThread, processId, threadId) = win32process.CreateProcess(None, cmd_as_str, None, None, True, win32process.CREATE_BREAKAWAY_FROM_JOB, None, None, startup)
    hJob = win32job.CreateJobObject(None, "")
    extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
    extended_info["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)
    win32job.AssignProcessToJobObject(hJob, hProcess)

    while True:
        exit_code = win32process.GetExitCodeProcess(hProcess)
        if exit_code != STILL_ACTIVE:
            if exit_code != 0:
                if exit_code == -1073741515:
                    raise RuntimeErrorWithExitCode(f"Could not start Dolphin!\n\nPlease install \"Visual C++ Redistributable Packages for Visual Studio 2013\" at https://www.microsoft.com/en-us/download/details.aspx?id=40784 in order to run the program's version of Dolphin.\n\n(Technical details: exit code: {exit_code} (0x{exit_code & 0xffffffff:08x}), command: {cmd_as_str})", exit_code)
                else:
                    raise RuntimeErrorWithExitCode(f"The following command returned with non-zero exit code {exit_code} (0x{exit_code & 0xffffffff:08x}): {cmd_as_str}", exit_code)
            break
            
        time.sleep(1)


def test_subprocess_as_job():
    run_subprocess_as_job(("../Dolphin-Lua-Core/Binary/x64/Dolphin.exe", "-b", "-e", "$i"))

if __name__ == "__main__":
    test_subprocess_as_job()
