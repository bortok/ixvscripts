#!/usr/bin/env python

#################################################################################
##
## File:   set_nto_config.py
## Date:   March 7, 2017
## Author: Fred Mota (fmota@ixiacom.com)
##
## History:
##
## Description:
## This script reads the configuration for all ports, port groups, and filters
## saved by the get_nto_config.py script.  After reading the configurtion for
## these objects, this script modifies each port, creates new port groups and
## cretes nw dynamic fiters with their with its correspoding properties read
## from the configuration file.
##
## This is useful when downgrading the version on a NTO, since it is not
## possible to import a configuration genearted by a newer release into an
## older release.
##
## (c) 1998-2017 Ixia. All rights reserved.
##
##############################################################################

import sys
import getopt
import threading
import json
from ksvisionlib import *

ports_writable_properties = {
    "afm_pipeline_direction",     # -> 'The property AFM_PIPELINE_DIRECTION can only be set on a port in port mode SIMPLEX.'
    "burst_buffer_settings",
    "connect_in_access_settings",
    "connect_out_access_settings",
    "copper_link_polling",
    #"custom_icon_id",
    "data_masking_settings",
    "dedup_settings",
    "description",
    "enabled",
    "erspan_strip_settings",
    "fabric_path_strip_settings",
    "filter_criteria",
    "filter_match_count_unit",
    "filter_mode",
    "filtering_direction",
    "force_link_up",
    "gtp_fd_settings",
    "gtp_strip_settings",
    "icon_type",
    "ignore_pause_frames",
    "is_shared",
    "keywords",
    "l2gre_strip_settings",
    "link_settings",
    "link_up_down_trap_enabled",
    "lldp_receive_enabled",
    "lldp_transmit_enabled",
    "media_type",
    #"mod_count",
    "mode",
    "modify_access_settings",
    "mpls_strip_settings",
    "name",
    "packet_length_trailer_settings",
    "resource_access_settings",
    "snmp_tag",
    "std_port_tagging_settings",
    "std_vlan_strip_settings",
    "timestamp_settings",
    "trailer_strip_settings",
    "trim_settings",
    "tunnel_termination_settings",
    "tx_light_status",
    "vntag_strip_settings",
    "vxlan_strip_settings"
}

port_groups_writable_properties = {
    ##"afm_pipeline_direction",     -> 'The property AFM_PIPELINE_DIRECTION is read-only for port groups and cannot be set.'
    "burst_buffer_settings",
    #"custom_icon_id",
    "data_masking_settings",
    "dedup_settings",
    "description",
    "erspan_strip_settings",
    "fabric_path_strip_settings",
    "failover_mode",
    "filter_criteria",
    "filter_mode",
    "filtering_direction",
    ##"force_link_up",              -> AFM module to non-AFM module?
    "gtp_strip_settings",
    "icon_type",
    "interconnect_info",
    "is_shared",
    "keywords",
    "l2gre_strip_settings",
    #"mod_count",
    #"mode",
    "mpls_strip_settings",
    "name",
    "packet_length_trailer_settings",
    #"port_list",
    "snmp_tag",
    "std_vlan_strip_settings",
    "timestamp_settings",
    "trailer_strip_settings",
    "trim_settings",
    ##"tx_light_status",            -> 'Cannot modify the transmit light status directly on a port group.'
    "vntag_strip_settings",
    "vxlan_strip_settings"
}

filters_writable_properties = {
    ##"application_forwarding_map", -> ATIP
    "connect_in_access_settings",
    "connect_out_access_settings",
    "criteria",
    "description",
    "dest_port_group_list",
    "dest_port_list",
    "keywords",
    "match_count_unit",
    #"mod_count",
    "mode",
    "modify_access_settings",
    "name",
    "resource_access_settings",
    "snmp_tag",
    "source_port_group_list",
    "source_port_list"
}

def setConfig(host_ip, port, username, password):

    f = open(host_ip + '_config.txt', 'r')
    config_txt = f.readline()
    config = json.loads(config_txt)
    f.close()

    nto = VisionWebApi(host=host_ip, username=username, password=password, port=port, debug=True, logFile="ixvision_set_nto_config_safe_debug.log")

    # Configure the icons
    for object_id in config:
        object = config[object_id]
        if object['type'] == 'icon':
            icon = nto.getIcon(object['name'])
            object['new_id'] = icon['id']

    # Configure the ports
    for object_id in config:
        object = config[object_id]
        if object['type'] == 'port':
            port = nto.getPort(object['name'])
            object['new_id'] = port['id']

            port_properties = {}
            for property in ports_writable_properties:
                if property in object['details']:
                    if (property != 'afm_pipeline_direction') or (property == 'afm_pipeline_direction' and object['details']['mode'] == 'SIMPLEX'):
                        port_properties[property] = object['details'][property]

#            if object['details']['custom_icon_id']:
#                port_properties['custom_icon_id'] = config[str(object['details']['custom_icon_id'])]['new_id']

            nto.modifyPort(str(port['id']), port_properties)

    # Configure the port groups
    for object_id in config:
        object = config[object_id]
        if object['type'] == 'port_group':
            port_group = nto.createPortGroup({'mode': object['details']['mode'], 'type': object['details']['type']})
            object['new_id'] = port_group['id']

            port_group_properties = {}
            for property in port_groups_writable_properties:
                if property in object['details']:
                    port_group_properties[property] = object['details'][property]

            port_group_properties['port_list'] = []
            for port_id in object['details']['port_list']:
                port_group_properties['port_list'].append(config[str(port_id)]['new_id'])

#            if object['details']['custom_icon_id']:
#                port_group_properties['custom_icon_id'] = config[str(object['details']['custom_icon_id'])]['new_id']

            nto.modifyPortGroup(str(port_group['id']), port_group_properties)

    # Configure the filters
    for object_id in config:
        object = config[object_id]
        if object['type'] == 'filter':
            filter = nto.createFilter({'mode': object['details']['mode'], 'criteria': object['details']['criteria']})
            object['new_id'] = filter['id']

            filter_properties = {}
            for property in filters_writable_properties:
                if property in object['details']:
                    filter_properties[property] = object['details'][property]

            filter_properties['dest_port_list'] = []
            for port_id in object['details']['dest_port_list']:
                filter_properties['dest_port_list'].append(config[str(port_id)]['new_id'])

            filter_properties['source_port_list'] = []
            for port_id in object['details']['source_port_list']:
                filter_properties['source_port_list'].append(config[str(port_id)]['new_id'])

            filter_properties['dest_port_group_list'] = []
            for port_group_id in object['details']['dest_port_group_list']:
                filter_properties['dest_port_group_list'].append(config[str(port_group_id)]['new_id'])

            filter_properties['source_port_group_list'] = []
            for port_group_id in object['details']['source_port_group_list']:
                filter_properties['source_port_group_list'].append(config[str(port_group_id)]['new_id'])

            nto.modifyFilter(str(filter['id']), filter_properties)


argv = sys.argv[1:]
username = ''
password = ''
host = ''
hosts_file = ''
config_file = ''
port = 8000

try:
    opts, args = getopt.getopt(argv,"u:p:h:f:r:", ["username=", "password=", "host=", "hosts_file=", "port="])
except getopt.GetoptError:
    print 'set_nto_config.py -u <username> -p <password> [-h <hosts> | -f <host_file>] [-r port]'
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-u", "--username"):
        username = arg
    elif opt in ("-p", "--password"):
        password = arg
    elif opt in ("-h", "--host"):
        host = arg
    elif opt in ("-f", "--hosts_file"):
        hosts_file = arg
    elif opt in ("-r", "--port"):
        port = arg

if username == '':
    print 'set_nto_config.py -u <username> -p <password> [-h <hosts> | -f <host_file>] [-r port]'
    sys.exit(2)

if password == '':
    print 'set_nto_config.py -u <username> -p <password> [-h <hosts> | -f <host_file>] [-r port]'
    sys.exit(2)

if (host == '') and (hosts_file == ''):
    print 'set_nto_config.py -u <username> -p <password> [-h <hosts> | -f <host_file>] [-r port]'
    sys.exit(2)

hosts_list = []
if (hosts_file != ''):
    f = open(hosts_file, 'r')
    for line in f:
        line = line.strip()
        if (line != '') and (line[0] != '#'):
            hosts_list.append(line.split(' '))
    f.close()
else:
    hosts_list.append([host, host])

threads_list = []
for host in hosts_list:
    host_ip = host[0]
    
    thread = threading.Thread(name=host, target=setConfig, args=(host_ip, port, username, password))
    threads_list.append(thread)

for thread in threads_list:
    thread.daemon = True
    thread.start()

try:
    while threading.active_count() > 1:
        for thread in threads_list:
            thread.join(1)
        sys.stdout.write('.')
        sys.stdout.flush()
except KeyboardInterrupt:
    print "Ctrl-c received! Sending kill to threads..."
    sys.exit()
print ""
