"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
import dateutil

from faraday_plugins.plugins.plugin import PluginXMLFormat
import re
import os
import xml.etree.ElementTree as ET

current_path = os.path.abspath(os.getcwd())

__author__ = "Blas"
__copyright__ = "Copyright (c) 2019, Infobyte LLC"
__credits__ = ["Blas"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Blas"
__email__ = "bmoyano@infobytesec.com"
__status__ = "Development"


class NessusParser:
    """
    The objective of this class is to parse an xml file generated by the nessus tool.

    TODO: Handle errors.
    TODO: Test nessus output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param nessus_filepath A proper simple report generated by nessus
    """

    def __init__(self, output):
        self.tree = ET.fromstring(output)
        self.tag_control = []
        for x in self.tree:
            self.tag_control.append(x)
        if self.tree:
            self.policy = self.getPolicy(self.tree)
            self.report = self.getReport(self.tree)
        else:
            self.policy = None
            self.report = None

    def getPolicy(self, tree):
        policy_tree = tree.find('Policy')
        return Policy(policy_tree)

    def getReport(self, tree):
        report_tree = tree.find('Report')
        return Report(report_tree)


class Policy():
    def __init__(self, policy_node):
        self.node = policy_node
        self.policy_name = self.node.find('policyName').text
        self.preferences = self.getPreferences(self.node.find('Preferences'))
        self.family_selection = self.getFamilySelection(self.node.find('FamilySelection'))
        self.individual_plugin_selection = self.getIndividualPluginSelection(
            self.node.find('IndividualPluginSelection'))

    def getPreferences(self, preferences):
        server_preferences = preferences.find('ServerPreferences')
        plugins_preferences = preferences.find('PluginsPreferences')
        server_preferences_all = []
        plugins_preferences_json = {}
        plugins_preferences_all = []
        for sp in server_preferences:
            sp_value = sp.find('value').text
            sp_name = sp.find('name').text
            server_preferences_all.append("Server Preferences name: {}, Server Preferences value: {}".format(sp_name,
                                                                                                             sp_value))
        for pp in plugins_preferences:
            for pp_detail in pp:
                plugins_preferences_json.setdefault(pp_detail.tag, pp_detail.text)
            plugins_preferences_all.append(plugins_preferences_json)
        return server_preferences_all, plugins_preferences_all

    def getFamilySelection(self, family):
        family_all = []
        for f in family:
            family_name = f.find('FamilyName').text
            family_value = f.find('Status').text
            family_all.append("Family Name: {}, Family Value: {}".format(family_name, family_value))
        return family_all

    def getIndividualPluginSelection(self, individual):
        item_plugin = []
        for i in individual:
            plugin_id = i.find('PluginId').text
            plugin_name = i.find('PluginName').text
            plugin_family = i.find('Family').text
            plugin_status = i.find('Status').text
            item_plugin.append("Plugin ID: {}, Plugin Name: {}, Family: {}, Status: {}".format(plugin_id, plugin_name,
                                                                                               plugin_family,
                                                                                               plugin_status))
        return item_plugin


class Report():
    def __init__(self, report_node):
        self.node = report_node
        self.report_name = self.node.attrib.get('name')
        self.report_host = self.node.find('ReportHost')
        self.report_desc = []
        self.report_ip = []
        self.report_serv = []
        self.report_json = {}
        if self.report_host is not None:
            for x in self.node:
                self.report_host_ip = x.attrib.get('name')
                self.host_properties = self.gethosttag(x.find('HostProperties'))
                self.report_item = self.getreportitems(x.findall('ReportItem'))
                self.report_ip.append(self.report_host_ip)
                self.report_desc.append(self.host_properties)
                self.report_serv.append(self.report_item)
                self.report_json['ip'] = self.report_ip
                self.report_json['desc'] = self.report_desc
                self.report_json['serv'] = self.report_serv
                self.report_json['host_end'] = self.host_properties.get('HOST_END')

        else:
            self.report_host_ip = None
            self.host_properties = None
            self.report_item = None
            self.report_json = None

    def getreportitems(self, items):
        result_item = []

        for item in items:
            self.port = item.attrib.get('port')
            self.svc_name = item.attrib.get('svc_name')
            self.protocol = item.attrib.get('protocol')
            self.severity = item.attrib.get('severity')
            self.plugin_id = item.attrib.get('pluginID')
            self.plugin_name = item.attrib.get('pluginName')
            self.plugin_family = item.attrib.get('pluginFamily')
            if item.find('plugin_output') is not None:
                self.plugin_output = item.find('plugin_output').text
            else:
                self.plugin_output = "Not Description"
            if item.find('description') is not None:
                self.description = item.find('description').text
            else:
                self.description = "Not Description"

            self.info = self.getinfoitem(item)
            result_item.append((self.port, self.svc_name, self.protocol, self.severity, self.plugin_id,
                                self.plugin_name, self.plugin_family, self.description, self.plugin_output, self.info))
        return result_item

    def getinfoitem(self, item):
        item_tags = {}
        for i in item:
            item_tags.setdefault(i.tag, i.text)
        return item_tags

    def gethosttag(self, tags):
        host_tags = {}
        for t in tags:
            host_tags.setdefault(t.attrib.get('name'), t.text)
        return host_tags

    def getnote(self):
        result = "El nombre es {}".format(self.report_name)
        return result


class NessusPlugin(PluginXMLFormat):
    """
    Example plugin to parse nessus output.
    """

    def __init__(self):
        super().__init__()
        self.extension = ".nessus"
        self.identifier_tag = "NessusClientData_v2"
        self.id = "Nessus"
        self.name = "Nessus XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "5.2.4"
        self.framework_version = "1.0.1"
        self.options = None
        self._current_output = None
        self._current_path = None
        self._command_regex = re.compile(
            r'^(nessus|sudo nessus|\.\/nessus).*?')
        self.host = None
        self.port = None
        self.protocol = None
        self.fail = None

    def canParseCommandString(self, current_input):
        if self._command_regex.match(current_input.strip()):
            return True
        else:
            return False

    def parseOutputString(self, output, debug=False):
        """
        This method will discard the output the shell sends, it will read it from
        the xml where it expects it to be present.

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """
        try:
            parser = NessusParser(output)
        except:
            print("Error parser output")
            return None

        if parser.report.report_json is not None:
            run_date = parser.report.report_json.get('host_end')
            if run_date:
                run_date = dateutil.parser.parse(run_date)
            for set_info, ip in enumerate(parser.report.report_json['ip'], start=1):
                if 'mac-address' in parser.report.report_json['desc'][set_info - 1]:
                    mac = parser.report.report_json['desc'][set_info - 1]['mac-address']
                else:
                    mac = ''
                if 'operating-system' in parser.report.report_json['desc'][set_info - 1]:
                    os = parser.report.report_json['desc'][set_info - 1]['operating-system']
                else:
                    os = None

                if 'host-ip' in parser.report.report_json['desc'][set_info - 1]:
                    ip_host = parser.report.report_json['desc'][set_info - 1]['host-ip']
                else:
                    ip_host = "0.0.0.0"
                if 'host-fqdn' in parser.report.report_json['desc'][set_info - 1]:
                    website = parser.report.report_json['desc'][set_info - 1]['host-fqdn']
                    host_name = []
                    host_name.append(parser.report.report_json['desc'][set_info - 1]['host-fqdn'])
                else:
                    website = None
                    host_name = None

                host_id = self.createAndAddHost(ip_host, os=os, hostnames=host_name, mac=mac)

                interface_id = self.createAndAddInterface(host_id, ip, ipv6_address=ip, mac=mac)
                cve = []
                for serv in parser.report.report_json['serv'][set_info -1]:
                    serv_name = serv[1]
                    serv_port = serv[0]
                    serv_protocol = serv[2]
                    serv_status = serv[3]
                    external_id = serv[4]
                    serv_description = serv[7]
                    cve.append(serv[8])
                    severity = serv[3]
                    desc = serv[8]

                    if serv_name == 'general':
                        ref = []
                        vulnerability_name = serv[5]
                        data = serv[9]
                        if not data:
                            continue
                        if 'description' in data:
                            desc = data['description']
                        else:
                            desc = "No description"
                        if 'solution' in data:
                            resolution = data['solution']
                        else:
                            resolution = "No Solution"
                        if 'plugin_output' in data:
                            data_po = data['plugin_output']
                        else:
                            data_po = "Not data"

                        risk_factor = "unclassified"
                        if 'risk_factor' in data:
                            risk_factor = data['risk_factor']
                        if risk_factor == 'None':
                            risk_factor = "info" # I checked several external id and most of them were info

                        if 'cvss_base_score' in data:
                            cvss_base_score = "CVSS :{}".format(data['cvss_base_score'])
                            ref.append(cvss_base_score)
                        else:
                            ref = []

                        policyviolations = []
                        if serv[6] == 'Policy Compliance':
                            # This condition was added to support CIS Benchmark in policy violation field.
                            risk_factor = 'info'
                            bis_benchmark_data = serv[7].split('\n')
                            policy_item = bis_benchmark_data[0]

                            for policy_check_data in bis_benchmark_data:
                                if 'ref.' in policy_check_data:
                                    ref.append(policy_check_data)

                            if 'FAILED' in policy_item:
                                risk_factor = 'high'
                                policyviolations.append(policy_item)

                            vulnerability_name = f'{serv[6]} {vulnerability_name} {policy_item}'

                        self.createAndAddVulnToHost(host_id,
                                                    vulnerability_name,
                                                    desc=desc,
                                                    severity=risk_factor,
                                                    resolution=resolution,
                                                    data=data_po,
                                                    ref=ref,
                                                    policyviolations=policyviolations,
                                                    external_id=external_id,
                                                    run_date=run_date)
                    else:
                        data = serv[9]
                        if not data:
                            continue
                        ref = []
                        vulnerability_name = serv[5]
                        if 'description' in data:
                            desc = data['description']
                        else:
                            desc = "No description"
                        if 'solution' in data:
                            resolution = data['solution']
                        else:
                            resolution = "No Solution"
                        if 'plugin_output' in data:
                            data_po = data['plugin_output']
                        else:
                            data_po = "Not data"

                        risk_factor = "info"
                        if 'risk_factor' in data:
                            risk_factor = data['risk_factor']

                        if risk_factor == 'None':
                            risk_factor = 'info'

                        if 'cvss_base_score' in data:
                            cvss_base_score = f"CVSS:{data['cvss_base_score']}"
                            ref.append(cvss_base_score)
                        if 'cvss_vector' in data:
                            cvss_vector = f"CVSSVECTOR:{data['cvss_vector']}"
                            ref.append(cvss_vector)
                        if 'see_also' in data:
                            ref.append(data['see_also'])
                        if 'cpe' in data:
                            ref.append(data['cpe'])
                        if 'xref' in data:
                            ref.append(data['xref'])

                        service_id = self.createAndAddServiceToInterface(host_id,
                                                                         interface_id,
                                                                         name=serv_name,
                                                                         protocol=serv_protocol,
                                                                         ports=serv_port)

                        if serv_name == 'www' or serv_name == 'http':
                            self.createAndAddVulnWebToService(host_id,
                                                              service_id,
                                                              name=vulnerability_name,
                                                              desc=desc,
                                                              data=data_po,
                                                              severity=risk_factor,
                                                              resolution=resolution,
                                                              ref=ref,
                                                              external_id=external_id,
                                                              website=website,
                                                              run_date=run_date)
                        else:
                            self.createAndAddVulnToService(host_id,
                                                           service_id,
                                                           name=vulnerability_name,
                                                           severity=risk_factor,
                                                           desc=desc,
                                                           ref=ref,
                                                           data=data_po,
                                                           external_id=external_id,
                                                           resolution=resolution,
                                                           run_date=run_date)
        else:
            ip = '0.0.0.0'
            host_id = self.createAndAddHost(ip, hostnames="Not Information")
            interface_id = self.createAndAddInterface(host_id, ip)

            service_id = self.createAndAddServiceToInterface(host_id, interface_id, name="Not Information")
            self.createAndAddVulnToService(host_id,
                                           service_id,
                                           name=parser.policy.policy_name,
                                           desc="No Description")


def createPlugin():
    return NessusPlugin()

# I'm Py3
