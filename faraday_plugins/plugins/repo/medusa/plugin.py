"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
import re
from faraday_plugins.plugins.plugin import PluginBase
from faraday_plugins.plugins.plugins_utils import resolve_hostname


__author__ = "Francisco Amato"
__copyright__ = "Copyright 2013, Faraday Project"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class MedusaParser:
    """
    The objective of this class is to parse an xml file generated by the medusa tool.

    @param medusa_filepath A proper simple report generated by medusa
    """

    def __init__(self, xml_output):
        self.srv = {
            'ftp': '21',  'http': '80', 'imap': '143', 'mssql': '1433', 'mysql': '3306',
            'ncp': '524', 'nntp': '119', 'pcanywhere': '5631', 'pop3': '110', 'postgres': '5432',
            'rexec': '512', 'rlogin': '513', 'rsh': '514', 'smbnt': 'smbnt', 'smtp': '25',
            'smtp-vrfy': 'smtp-vrfy', 'snmp': '161', 'ssh': '22', 'svn': '3690',
            'telnet': '23', 'vmauthd': 'vmauthd', 'vnc': '5900', 'web-form': 'web-form',
            'wrapper': 'wrapper'
        }

        lines = xml_output.splitlines()
        self.items = []
        
        for l in lines:

            reg = re.search("ACCOUNT FOUND: \[([^$]+)\] Host: ([^$]+) User: ([^$]+) Password: ([^$]+) \[SUCCESS\]", l)
            if reg:
        
                item = {
                    'service': reg.group(1),
                    'host': reg.group(2),
                    'user': reg.group(3),
                    'pass': reg.group(4)
                }
                item['ip'] = resolve_hostname(item['host'])
                item['port'] = self.srv[item['service']]
                self.items.append(item)


class MedusaPlugin(PluginBase):
    """
    Example plugin to parse medusa output.
    """

    def __init__(self):
        super().__init__()
        self.id = "Medusa"
        self.name = "Medusa Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "2.1.1"
        self.options = None
        self._command_regex = re.compile(r'^(sudo medusa|sudo \.\/medusa|medusa|\.\/medusa)\s+.*?')
        self.host = None
        self.port = ""
        self._use_temp_file = True
        self._temp_file_extension = "txt"
        self.xml_arg_re = re.compile(r"^.*(-O\s*[^\s]+).*$")

    def parseOutputString(self, output):
        """
        This method will discard the output the shell sends, it will read it from
        the xml where it expects it to be present.

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """
        parser = MedusaParser(output)
        
        for item in parser.items:
        
            h_id = self.createAndAddHost(item['ip'])
            if self._isIPV4(item['ip']):
                i_id = self.createAndAddInterface(
                    h_id,
                    item['ip'],
                    ipv4_address=item['ip'],
                    hostname_resolution=[item['host']])
            else:
                i_id = self.createAndAddInterface(
                    h_id,
                    item['ip'],
                    ipv6_address=item['ip'],
                    hostname_resolution=[item['host']])

            port = self.port if self.port else item['port']

            s_id = self.createAndAddServiceToInterface(
                h_id,
                i_id,
                item['service'],
                ports=[port],
                protocol="tcp",
                status="open")

            self.createAndAddCredToService(
                h_id,
                s_id,
                item['user'],
                item['pass'])

            self.createAndAddVulnToService(h_id,
                s_id,
                "Weak Credentials",
                "[medusa found the following credentials]\nuser:%s\npass:%s" % (item['user'], item['pass']),
                severity="high")

        del parser

    def processCommandString(self, username, current_path, command_string):
        super().processCommandString(username, current_path, command_string)
        self.port = ""
        arg_match = self.xml_arg_re.match(command_string)

        mreg = re.search(r"\-n( |)([\d]+)", command_string)
        if mreg:
            self.port = mreg.group(2)

        if arg_match is None:
            return re.sub(r"(^.*?medusa?)", r"\1 -O %s" % self._output_file_path, command_string)
        else:
            return re.sub(arg_match.group(1), r"-O %s" % self._output_file_path, command_string)

    def _isIPV4(self, ip):
        if len(ip.split(".")) == 4:
            return True
        else:
            return False

    def setHost(self):
        pass


def createPlugin():
    return MedusaPlugin()
