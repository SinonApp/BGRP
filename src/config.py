# Interface listen traffic
# this interface will be used for sniffing packets
listen_interface = 'ens3'
# this param set sniffing incoming packets
listen_direction = 'out' # in, out, inout

# Route table for adding routes into
# you can set route table, using mark from: Wireguard, Another marks, etc.
route_table = 0

# Active gateways with number route_table
# route_table creating authomatic.
gateways = {
	'10.10.0.2': 111,
	'10.10.0.3': 222,
	'10.10.0.4': 333,
}

# List with static routes
# will be added when start service, and will remove when stoping
static_routes = {
	'1.1.1.1/32': 'default',
	'192.168.0.0/23': '10.10.0.3'
}

# List bypass destination ips, for allow this traffic from default gateway
# this addresses don't be sniffed and adding in routing table
bypass_list = [
	'1.1.1.1',
	'8.8.8.8',
]
