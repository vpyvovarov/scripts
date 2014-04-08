#!/usr/local/bin/env python
import subprocess
import requests
import re
import argparse
import getpass

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument("-p", "--portal_hostname", type=str,
    help="Hostname of EQ portal from which we get hostnames to restart")

arg_parser.add_argument("-u", "--username", type=str,
    help="Username for EQ portal. username@llnw.com")

arg_parser.add_argument("-p", "--password", type=str,
    help="Password for EQ")

arg_parser.add_argument("-f", "--hostname_file", type=str, default='host_to_restart.txt',
    help="File for storing hostname of boxes to be restarted")

arg_parser.add_argument("-g", "--gather_hostnames", action="store_true",
    help="Generate list of hosts from portal page")

arg_parser.add_argument("-t", "--client_type", type=str,
    help="Which instance of client need to be restarted")

args = arg_parser.parse_args()

url = 'https://%s/portal/monitoring/hosts/griddata' %args.portal_hostname
post_data =  {'page': 1, 'rp': 100, 'sortname': 'undefined', 'sortorder': 'undefined', 'query': '', 'qtype': '', 'statuses': 2, 'hostname': '', 'serviceStatus': 'IN_SERVICE_YES', 'ticketStatus': 'HAS_TICKET_NO'}

if args.get('password', False):
    args.password = getpass.getpass()

response = requests.post(url, auth=(args.username, args.password), allow_redirects=True,  verify=False,  data=post_data)
hosts_info_list = {item['cell']['hostname']: item['cell']['hm_delay'] for item in response.json['rows']}

def get_hostnames(hostname_file):
    hostnames=open(hostname_file,'w+')
    for host, time in hosts_info_list.iteritems():
        time=re.findall('(\d+)[m|d|h]*', time)
        if time:
            if len(time)>1 or time[-1]>30:
                hostnames.write(host + '\n')
    hostnames.close()

if args.gather_hostname:
    get_hostnames(args.hostname_file)

hostnames=open(args.hostname_file,'w+').readlines()

if args.client_type == 'billing':
    command = 'service eqbilling restart'

if args.client_type == 'reporting':
    command = 'service edgequeryd restart'

if args.client_type == 'fcds':
    command = '/usr/local/llnw/edgequery/etc/init.d/eqbilling-wrapper restart'

for host in hostnames:
    p = subprocess.Popen(["ssh", "root@"+host.strip(), command], stdout=subprocess.PIPE)
    print p.communicate()
