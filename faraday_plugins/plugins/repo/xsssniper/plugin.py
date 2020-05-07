"""
Faraday Penetration Test IDE
Copyright (C) 2017  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
import re

__author__ = "Roberto Focke"
__copyright__ = "Copyright (c) 2017, Infobyte LLC"
__license__ = ""
__version__ = "1.0.0"

from faraday_plugins.plugins.plugin import PluginBase
from faraday_plugins.plugins.plugins_utils import resolve_hostname


class xsssniper(PluginBase):

    def __init__(self):
        super().__init__()
        self.id = "xsssniper"
        self.name = "xsssniper"
        self.plugin_version = "0.0.1"
        self.version = "1.0.0"
        self.protocol = "tcp"
        self._command_regex = re.compile(r'^(sudo xsssniper |xsssniper |sudo xsssniper\.py |xsssniper\.py |sudo python '
                                         r'xsssniper\.py |.\/xsssniper\.py |python xsssniper\.py )')

    def parseOutputString(self, output, debug=False):
        parametro = []
        lineas = output.split("\n")
        aux = 0
        for linea in lineas:
            if not linea:
                continue
            linea = linea.lower()
            if ((linea.find("target:")>0)):
                url = re.findall('(?:[-\w.]|(?:%[\da-fA-F]{2}))+', linea)
                print(url)
                host_id = self.createAndAddHost(url[3])
                address = resolve_hostname(url[3])
                interface_id = self.createAndAddInterface(host_id,address,ipv4_address=address,hostname_resolution=url[3])
            if ((linea.find("method")>0)):
                list_a = re.findall("\w+", linea)
                metodo= list_a[1]
            if ((linea.find("query string:")>0)):
                lista_parametros=linea.split('=')
                aux=len(lista_parametros)
            if ((linea.find("param:")>0)):
                list2 = re.findall("\w+",linea)
                parametro.append(list2[1])
                service_id = self.createAndAddServiceToInterface(host_id, interface_id, self.protocol, 'tcp',
                                                                 ports=['80'], status='Open', version="", description="")
        if aux != 0:
            self.createAndAddVulnWebToService(host_id, service_id, name="xss", desc="XSS", ref='', severity='med',
                                              website=url[0], path='', method=metodo, pname='',
                                              params=''.join(parametro), request='', response='')


def createPlugin():
    return xsssniper()

# I'm Py3
