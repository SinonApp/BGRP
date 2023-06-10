#!/usr/bin/env python3

import subprocess
import concurrent.futures
import time
import argparse
import sys

parser = argparse.ArgumentParser(description='Best Gateway Routing Protocol')
parser.add_argument('--config', help='path to config.py')

args = parser.parse_args()
if args.config:
	import importlib.util
	spec = importlib.util.spec_from_file_location("config", args.config)
	config = importlib.util.module_from_spec(spec)
	sys.modules["config"] = config
	spec.loader.exec_module(config)
else:
	sys.exit()

checked = {

}

def add_static_route(network, gateway, mark):
	try:
		subprocess.check_output(f"ip route del {network} via {gateway} table {mark}".split(), stderr=subprocess.DEVNULL)
		subprocess.check_output(f"ip route add {network} via {gateway} table {mark}".split(), stderr=subprocess.DEVNULL)
	except:
		pass

def del_static_route(network, gateway, mark):
	try:
		subprocess.check_output(f"ip route del {network} via {gateway} table {mark}".split(), stderr=subprocess.DEVNULL)
	except:
		pass

def add_gateway_checking_mark(gateway, mark):
	try:
		subprocess.check_output(f"ip rule add fwmark {mark} lookup {mark}".split(), stderr=subprocess.DEVNULL)
		subprocess.check_output(f"ip route add 0.0.0.0/0 via {gateway} table {mark}".split(), stderr=subprocess.DEVNULL)
	except:
		pass

def del_gateway_checking_mark(gateway, mark):
	try:
		subprocess.check_output(f"ip route del 0.0.0.0/0 via {gateway} table {mark}".split(), stderr=subprocess.DEVNULL)
		subprocess.check_output(f"ip route flush table {mark}".split(), stderr=subprocess.DEVNULL)
		subprocess.check_output(f"ip rule del fwmark {mark} lookup {mark}".split(), stderr=subprocess.DEVNULL)
	except:
		pass

def first_ping(target_ip, gateway_mark):
	try:
		output = subprocess.check_output(['ping', '-c', '1', '-W', '1', '-q', '-i', '0.2', '-m', str(gateway_mark), target_ip])
		if "0% packet loss" in output.decode():
			return True
		return False
	except:
		return False

def average_ping_time(target_ip, gateway_mark):
	if first_ping(target_ip, gateway_mark):
		try:
			command = ['ping', '-c', '3', '-W', '1', '-q', '-i', '0.2', '-m', str(gateway_mark), target_ip]
			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
			output, _ = process.communicate()
			output = output.decode('utf-8')

			avg_ping_time = None
			lines = output.strip().split('\n')
			for line in lines:
				if 'rtt' in line:
					parts = line.split('/')
					if len(parts) >= 5:
						avg_ping_time = float(parts[4])
					break
			return avg_ping_time
		except:
			return False
	return False

def check_target_in_checked(target_ip):
	if target_ip in checked:
		if int(time.time()) - checked[target_ip] < 1800:
			return True
	else:
		checked[target_ip] = int(time.time())

	return False

def add_route(target_ip, gateway):
	if gateway != 'default':
		subprocess.check_output(f"ip route add {target_ip}/32 via {gateway} table {route_table}".split(), stderr=subprocess.DEVNULL)

def del_route(target_ip):
	try:
		subprocess.check_output(f"ip route del {target_ip}/32 table {route_table}".split(), stderr=subprocess.DEVNULL)
	except:
		pass

def detect_forwarding_ips():
	print("[!][BGRP] Adding tables gateways")
	for gateway in config.gateways:
		del_gateway_checking_mark(gateway, config.gateways[gateway])
		add_gateway_checking_mark(gateway, config.gateways[gateway])

	print("[!][BGRP] Adding static routes")
	for static in config.static_routes:
		add_static_route(static, config.static_routes[static], config.route_table)

	try:
		process = subprocess.Popen(['tcpdump', '-i', config.listen_interface, '-Q', config.listen_direction, '-nn'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
		print("[*][BGRP] Detecting forwarding IPs...")
	except Exception as e:
		print(f"[X][BGRP] Error sniffing traffic: {str(e)}")
		sys.exit(1)

	while True:
		try:
			output = process.stdout.readline().decode('utf-8').strip()

			if output and 'IP' in output:
				parts = output.split()
				target_ip = None
				if len(parts[4].split('.')) > 4:
					target_ip = '.'.join(parts[4].split('.')[:-1:])
				elif len(parts[4].split('.')) == 4 and '::' not in parts[4]:
					target_ip = '.'.join(parts[4].split('.')[::])
				else:
					continue

				target_ip = target_ip.replace(':', '')
				if check_target_in_checked(target_ip): continue
				if target_ip in config.bypass_list: continue

				avg_ping_times = {}
				with concurrent.futures.ThreadPoolExecutor() as executor:
					ping_tasks = {executor.submit(average_ping_time, target_ip, config.gateways[gateway]): gateway for gateway in config.gateways}
					for task in concurrent.futures.as_completed(ping_tasks):
						gateway = ping_tasks[task]
						try:
							avg = task.result()
							if avg != False:
								avg_ping_time = avg
								avg_ping_times[gateway] = avg_ping_time
							else:
								avg_ping_times[gateway] = 100000
						except Exception as e:
							print(f"[X][BGRP] Error occurred for gateway {gateway}: {str(e)}")

				sorted_gateways = sorted(avg_ping_times, key=avg_ping_times.get)
				if len(sorted_gateways) >= 0:
					best_gateway = sorted_gateways[0]
					print(f"[+][BGRP] Best gateway	{best_gateway}	for	{target_ip}")
					del_route(target_ip)
					add_route(target_ip, best_gateway)
		except KeyboardInterrupt:
			break
		except Exception as e:
			print(f"[X][BGRP] Unknown error: {str(e)}")

	print("[!][BGRP] Clearing static routes")
	for static in config.static_routes:
		del_static_route(static, config.static_routes[static], config.route_table)

	print("[!][BGRP] Clearing tables gateways")
	for gateway in config.gateways:
		del_gateway_checking_mark(gateway, config.gateways[gateway])
		add_gateway_checking_mark(gateway, config.gateways[gateway])

detect_forwarding_ips()
