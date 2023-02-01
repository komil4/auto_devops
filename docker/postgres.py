import os
from docker import docker_compose


class Postgres:
    def __init__(self, network, name='postgres_db', image='postgres:latest',
                 main_path='/opt', start_script_dir='./scripts/postgres', database_names=[],
                 root_username='admin', root_password='Admin123'):
        self.name = name
        self.image = image
        self.path = os.path.join(main_path, 'postgresql')
        self.start_script_dir = start_script_dir
        self.root_username = root_username
        self.root_password = root_password
        self.database_names = database_names
        self.network = network

    def add_service_to_compose(self, compose):
        postgres_db = docker_compose.ComposeService(self.name, self.image)
        postgres_db.set_hostname(self.name)
        postgres_db.set_restart('always')
        postgres_db.set_container_name(self.name)
        postgres_db.add_volume(self.path, '/var/lib/postgresql')
        postgres_db.add_volume(self.start_script_dir, '/docker-entrypoint-initdb.d')
        postgres_db.add_environment('POSTGRES_USER', self.root_username)
        postgres_db.add_environment('POSTGRES_PASSWORD', self.root_password)
        multiple_databases = ''
        for database_name in self.database_names:
            multiple_databases = f"{database_name}:{self.root_username}" if multiple_databases == '' \
                else f"{multiple_databases},{database_name}:{self.root_username}"
        postgres_db.add_environment('POSTGRES_MULTIPLE_DATABASES', multiple_databases)
        postgres_db.add_network(self.network)
        compose.add_service(postgres_db)

    def start_initialization(self):
        return 0
