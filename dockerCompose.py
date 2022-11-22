SEP = ':'
TAB = '  '


def get_conform_str(name, value='', space=' ', value_sep='\'', global_sep=''):
	return f'{global_sep}{name}{SEP}{space}{value_sep}{value}{value_sep}{global_sep}' if value != '' else f'{name}{SEP}'


def write_line(file, line, tabs=0, prefix=''):
	new_line = ''
	new_line = new_line.join([TAB for _ in range(tabs)])
	new_line = f'{new_line}{prefix}{line}\n'
	file.write(new_line)


class ComposeStruct:
	def __init__(self, version='3.7'):
		self.version = version
		self.services = []
		self.volumes = []
		self.configs = []
		self.secrets = []
		self.networks = []

	def save_file(self, path, filename='docker-compose'):
		with open(f'{path}/{filename}.yml', 'w') as file:
			write_line(file, get_conform_str('version', self.version))
			write_line(file, get_conform_str('services'))

			for service in self.services:
				service.write_service_to_file(file)

			write_line(file, get_conform_str('networks'))
			for network in self.networks:
				network.write_network_to_file(file)

	def add_service(self, service):
		self.services.append(service)

	def add_network(self, network):
		self.networks.append(network)


class ComposeService:
	def __init__(self, name, image):
		self.service_name = name
		self.image = image
		self.restart = ''
		self.hostname = ''
		self.container_name = ''
		self.environment = []
		self.ports = []
		self.depends_on = []
		self.volumes = []
		self.networks = []
		self.variables = ['image', 'restart', 'hostname', 'container_name']
		self.collections = ['ports', 'depends_on', 'volumes', 'networks']

	def __getitem__(self, item):
		if item == 'image':
			return self.image
		elif item == 'restart':
			return self.restart
		elif item == 'hostname':
			return self.hostname
		elif item == 'container_name':
			return self.container_name
		elif item == 'ports':
			return self.ports
		elif item == 'depends_on':
			return self.depends_on
		elif item == 'volumes':
			return self.volumes
		elif item == 'networks':
			return self.networks
		else:
			return None

	def set_restart(self, restart):
		self.restart = restart

	def set_hostname(self, hostname):
		self.hostname = hostname

	def set_container_name(self, name):
		self.container_name = name

	def add_environment(self, name, value):
		self.environment.append({name: value})

	def add_port(self, host_port, container_port):
		self.ports.append({host_port: container_port})

	def add_depends_on(self, name, value=''):
		self.depends_on.append({name: value})

	def add_volume(self, host_volume, container_volume):
		self.volumes.append({host_volume: container_volume})

	def add_network(self, network):
		if isinstance(network, ComposeNetwork):
			self.networks.append(network.network_name)
		else:
			self.networks.append(network)

	def write_service_to_file(self, file):
		write_line(file, get_conform_str(self.service_name), 1)

		for var in self.variables:
			if self[var] != '':
				write_line(file, get_conform_str(var, self[var]), 2)

		self.write_environment_to_file(file)

		for collection in self.collections:
			if len(self[collection]) > 0:
				write_line(file, get_conform_str(collection), 2)
				for var in self[collection]:
					if isinstance(var, dict):
						for d in var:
							if collection == 'ports':
								write_line(file, get_conform_str(d, var[d], '', '', '\''), 3, '- ')
							elif var[d] == '':
								write_line(file, d, 3, '- ')
							else:
								write_line(file, get_conform_str(d, var[d]), 3, '- ')
					else:
						write_line(file, var, 3, '- ')

	def write_environment_to_file(self, file):

		if len(self.environment) == 0:
			return

		write_line(file, get_conform_str('environment'), 2)

		for p in self.environment:
			if isinstance(p, dict):
				for v in p:
					write_line(file, get_conform_str(v), 3)
					value = p[v]
					if isinstance(value, dict):
						for l in value:
							write_line(file, ''.join([l,
							                          ' \'',
							                          value[l],
							                          '\'']), 4)
			else:
				write_line(file, get_conform_str(p), 3, '- ')


class ComposeNetwork:
	def __init__(self, network_name, name):
		self.network_name = network_name
		self.name = name

	def write_network_to_file(self, file):
		write_line(file, get_conform_str(self.network_name), 1)
		write_line(file, get_conform_str('name', self.name), 2)
