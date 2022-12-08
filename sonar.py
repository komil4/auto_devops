import os
import docker_compose
from sonarqube import SonarQubeClient


class SonarQube:
	def __init__(self, network, port='9000', db_url='jdbc:postgresql://postgres_db:5432/sonarqube',
	             db_username='sonarqube', db_password='admin', name='sonarqube', image='sonarqube:latest',
	             main_path='/opt'):
		self.name = name
		self.image = image
		self.port = port
		self.db_url = db_url
		self.db_username = db_username
		self.db_password = db_password
		self.path = os.path.join(main_path, 'gitlab-runner')
		self.data_path = os.path.join(main_path, '/sonarqube/data')
		self.extensions_path = os.path.join(main_path, '/sonarqube/extensions')
		self.logs_path = os.path.join(main_path, '/sonarqube/logs')
		self.network = network
		self.sonar_qube_api = None
		self.access_token = ''
		self.projects = []

	def add_service_to_compose(self, compose, db_name='postgresql'):
		sonarqube = docker_compose.ComposeService(self.name, self.image)
		sonarqube.set_hostname(self.name)
		sonarqube.set_restart('always')
		sonarqube.set_container_name(self.name)
		sonarqube.add_depends_on(db_name)
		sonarqube.add_port(self.port,'9000')
		sonarqube.add_environment('SONARQUBE_JDBC_USERNAME', self.db_username)
		sonarqube.add_environment('SONARQUBE_JDBC_PASSWORD', self.db_password)
		sonarqube.add_environment('SONARQUBE_JDBC_URL', self.db_url)
		sonarqube.add_volume(self.data_path, '/opt/sonarqube/data')
		sonarqube.add_volume(self.extensions_path, '/opt/sonarqube/extensions')
		sonarqube.add_volume(self.logs_path, '/opt/sonarqube/logs')
		sonarqube.add_network(self.network)
		compose.add_service(sonarqube)

	def start_initialization(self, url, projects):
		self.sonar_qube_api = SonarQubeApi(f"http://{url}:{self.port}")
		for project in projects:
			project_key = self.sonar_qube_api.create_project(project)
			self.projects.append({'key': project_key, 'name': project})
		self.access_token = self.sonar_qube_api.create_access_token()

class SonarQubeApi:
	def __init__(self, url='http://localhost:9000', username='admin', password='admin'):
		self.sonar = SonarQubeClient(sonarqube_url=url, username=username, password=password)

	def create_project(self, key='my_project', name='my project'):
		self.sonar.projects.create_project(project=key, name=name, visibility="public")
		return key

	def create_access_token(self):
		return self.sonar.user_tokens.generate_user_token("Gitlab token")

		
