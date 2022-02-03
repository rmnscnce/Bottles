# terminal.py
#
# Copyright 2020 brombinmirko <send@mirko.pm>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess

from bottles.backend.logger import Logger # pyright: reportMissingImports=false

logging = Logger()


class TerminalUtils():
    '''
    This class is used to launch commands in the system terminal.
    It will loop all the "supported" terminals to find the one
    that is available, so it will be used to launch the command.
    '''
    colors = {
        "default": "#00ffff #2b2d2e",
        "debug": "#ff9800 #2e2c2b",
    }

    terminals = [
        ['easyterm.py', '-d -p "%s" -c %s'],
        ['xterm', '-e %s'],
        ['konsole', '-e %s'],
        ['gnome-terminal', '-- %s'],
        ['xfce4-terminal', '-e %s'],
        ['mate-terminal', '--command %s'],
        ['tilix', '-- %s'],
        ['qterminal', '--execute %s'],
        ['lxterminal', '-e %s'], 
    ]

    def check_support(self):
        for terminal in self.terminals:
            terminal_check = subprocess.Popen(
                f"command -v {terminal[0]} > /dev/null && echo 1 || echo 0",
                shell=True,
                stdout=subprocess.PIPE
            ).communicate()[0].decode("utf-8")

            if "1" in terminal_check:
                self.terminal = terminal
                return True

        return False

    def execute(self, command, env={}, colors="default"):
        if not self.check_support():
            logging.warning("Terminal not supported.")
            return False
        
        if colors not in self.colors:
            colors = "default"
            
        colors = self.colors[colors]
        
        if self.terminal[0] == 'easyterm.py':
            command = ' '.join(self.terminal) % (colors, f"bash -c '{command}'")
            if "ENABLE_BASH" in os.environ:
                command = ' '.join(self.terminal) % (colors, f"bash")
        elif self.terminal[0] == 'xfce4-terminal':
            command = ' '.join(self.terminal) % "'sh -c %s'" % f'"{command}"'
        else:
            command = ' '.join(self.terminal) % f"'bash -c {command}'"
        subprocess.Popen(
            command,
            shell=True,
            env=env,
            stdout=subprocess.PIPE
        ).communicate()[0].decode("utf-8")

        return True