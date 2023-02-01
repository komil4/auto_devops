from docker import docker_compose


class PgAdmin:
    def __init__(self, network, port='2080', email='mail@mail.com',
                 password='admin', name='pgadmin', image='dpage/pgadmin4:latest'):
        self.name = name
        self.image = image
        self.port = port
        self.email = email
        self.password = password
        self.network = network

    def add_service_to_compose(self, compose):
        pgadmin = docker_compose.ComposeService(self.name, self.image)
        pgadmin.set_restart('always')
        pgadmin.set_container_name(self.name)
        pgadmin.add_environment('PGADMIN_DEFAULT_EMAIL', self.email)
        pgadmin.add_environment('PGADMIN_DEFAULT_PASSWORD', self.password)
        pgadmin.add_port(self.port, '80')
        pgadmin.add_network(self.network)
        compose.add_service(pgadmin)

    def start_initialization(self):
        return 1


