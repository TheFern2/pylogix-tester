"""
   Originally created by Fernando B.
   Updated and maintained by Fernando B. (fernandobe+git@protonmail.com)
   Copyright 2019 Fernando Balandran
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from pylogix import PLC
from ping3 import ping
import sys
import datetime
import socket
import subprocess
import platform
import ipaddress

host_ip = ''
controller_ip = ''
controller_slot = ''
comm = PLC()
log = open("log.txt", "a+")
CODE_VERSION = "1.0.3"
now = datetime.datetime.now()
check_error_log = False
system_ready = False


def read_tag(tag):
    return comm.Read(tag)


def get_host_ip():
    global host_ip
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
    except Exception as e:
        check_error_log = True
        print("Error: %s" % (e))
        log.write("Error: %s %s\n" % (now.strftime("%c"), e))
        log.flush()


def check_pip_pylogix():

    installed_packages = None

    try:
        reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
        installed_packages = [r.decode().split('==')[0] for r in reqs.split()]
    except Exception as e:
        check_error_log = True
        print("Error: %s" % (e))
        log.write("Error: %s %s\n" % (now.strftime("%c"), e))
        log.flush()

    if 'pylogix' in installed_packages:
        print("Info: pylogix is installed on system with pip")
        log.write("Info: %s pylogix is installed on system with pip\n" %
                  (now.strftime("%c")))
        log.flush()
    else:
        check_error_log = True
        print("Error: pylogix was not found on system!")
        log.write("Error: %s pylogix was not found on system!\n" %
                  (now.strftime("%c")))
        log.flush()


def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False


if __name__ == "__main__":

    ascii_art = """
             _             _        _            _
            | |           (_)      | |          | |
 _ __  _   _| | ___   __ _ ___  __ | |_ ___  ___| |_ ___ _ __
| '_ \| | | | |/ _ \ / _` | \ \/ / | __/ _ \/ __| __/ _ \ '__|
| |_) | |_| | | (_) | (_| | |>  <  | ||  __/\__ \ ||  __/ |
| .__/ \__, |_|\___/ \__, |_/_/\_\  \__\___||___/\__\___|_|
| |     __/ |         __/ |
|_|    |___/         |___/
    """

    print(ascii_art)
    print("pylogix-tester " + CODE_VERSION)
    print("Author: Fernando Balandran")
    print("Source: " + "https://github.com/kodaman2/pylogix-tester")

    controller_ip = input("Enter controller ip: ")

    # ensure ip input is valid
    try:
        ipaddress.ip_address(controller_ip)
    except ValueError as e:
        print('%s' % (e))
        log.write('Error: %s %s\n' %
                  (now.strftime("%c"), e))
        log.flush()
        input("Program will exit now. Press Enter")
        sys.exit()

    try:
        controller_slot = int(input("Enter controller slot: "))
    except ValueError as e:
        print("Slot needs to be an integer")
        log.write("Error: %s Slot needs to be an integer\n" %
                  (now.strftime("%c")))
        input("Program will exit now. Press Enter")
        log.flush()
        sys.exit()
    except TypeError as e:
        print("Slot needs to be an integer")
        log.write("Error: %s Slot needs to be an integer\n" %
                  (now.strftime("%c")))
        input("Program will exit now. Press Enter")
        log.flush()
        sys.exit()

    comm.IPAddress = controller_ip
    comm.ProcessorSlot = controller_slot

    if ping(controller_ip) is None:
        check_error_log = True
        print("PLC unreachable, check IP or network settings!")
        input("Program will exit now. Press Enter")
        log.write("Error: %s PLC unreachable, check IP or network settings!\n" % (
            now.strftime("%c")))
        log.flush()
        sys.exit()

    is_micro800 = yes_or_no("Is this a Micro8xx PLC?")
    comm.Micro800 = is_micro800

    # discover devices
    devices = comm.Discover()

    for device in devices.Value:
        print(device.IPAddress)
        print('  Product Code: ' + device.ProductName +
              ' ' + str(device.ProductCode))
        print('  Vendor/Device ID:' + device.Vendor + ' ' + str(device.DeviceID))
        print('  Revision/Serial:' + device.Revision + ' ' + device.SerialNumber)
        print('')

    # get plc time for clx, and compact
    if not is_micro800:
        response = comm.GetPLCTime()
        print(response.Value)

    # ask for a controller / global tag
    controller_tag = input(
        """Enter a controller tag (CLX/Compactlogix), or global variable (Micro8xx):
        Examples:
        tag_name
        array_name[index]
        udt_name.tag_member\n
        """)

    # using new 0.4.0 response object
    # fetch one controller/global tag
    response = read_tag(controller_tag)
    if response.Value is not None:
        print(response.TagName, "=", response.Value, "\n")
        log.write("Info: %s %s = %s\n" %
                  (now.strftime("%c"), response.TagName, response.Value))
        log.flush()
        system_ready = True
    else:
        check_error_log = True
        print(response.TagName, response.Status)
        log.write("Error: %s %s %s\n" %
                  (now.strftime("%c"), response.TagName, response.Status))
        log.flush()

    # ask for a program tag, micro8xx doe not have program tags
    if not is_micro800:
        program_tag = input("""Enter a program tag:
        Examples:
        MyProgram.my_tag
        MyProgram.some_array[index]
        MyProgram.some_udt.tag_member\n
        """)

        response = read_tag("Program:" + program_tag)
        if response.Value is not None:
            print(response.TagName, "=", response.Value, "\n")
            log.write("Info: %s %s = %s\n" %
                      (now.strftime("%c"), response.TagName, response.Value))
            log.flush()
            system_ready = True
        else:
            check_error_log = True
            print(response.TagName, response.Status)
            log.write("Error: %s %s %s\n" %
                      (now.strftime("%c"), response.TagName, response.Status))
            log.flush()

    # check python installation
    print("Checking python on path")
    py_version = sys.version_info
    if py_version:
        print("Info: Python found on path: %s.%s\n" %
              (py_version[0], py_version[1]))
        log.write("Info: %s Python found on path: %s.%s\n" %
                  (now.strftime("%c"), py_version[0], py_version[1]))
        log.flush()
    else:
        check_error_log = True
        print("Please install python https://www.python.org/downloads/")
        log.write("Error: %s Please install python\n" % (now.strftime("%c")))
        log.flush()

    # System Checks
    # check_pip_pylogix() # giving issues with compiled exe
    get_host_ip()
    print("Host IP", host_ip)
    log.write("Info: %s %s\n" % (now.strftime("%c"), host_ip))
    print("OS Platform", platform.system())
    log.write("Info: %s %s\n" % (now.strftime("%c"), platform.system()))

    rocket_ship_ascii = """
                 .
           .d$ .
           d$$  :
          .$$$
          :$$$   :
          $$$$   :
          $$$$   :
         .$$$$
         :$$$$    :
         :$$$$    :
         $$$$$    :
         $$$$$    :
         :    $$$$$
         :    $$$$$
         :    $$$$$
        .:    $$$$$.
       / :    $$$$: \\
      /  :    $$$$:  \\
     '        $$$$`   '
     |    :   $$$$    |
     |   /:   $$$$\   |
     |  /     $$$` \  |
     |_/   :__$$P   \_|
    """

    error_ascii = """
    ───────────████████
    ──────────███▄███████
    ──────────███████████
    ──────────███████████
    ──────────██████
    ──────────█████████
    █───────███████
    ██────████████████
    ███──██████████──█
    ███████████████
    ███████████████
    ─█████████████
    ──███████████
    ────████████
    ─────███──██
    ─────██────█
    ─────█─────█
    ─────██────██
    """

    if system_ready:
        print(rocket_ship_ascii)
        print("System is ready for take off!")
        log.write("Info: %s System is ready for take off!\n" %
                  (now.strftime("%c")))
    else:
        print("System error, good luck next time!")
        print(error_ascii)

    if check_error_log:
        print("Check error log!")

    log.close()

    input("Hit Enter to Continue")
