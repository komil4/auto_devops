import os
import docker_compose


class GitlabRunner:
	def __init__(self, network, gitlab_hostname, name='gitlab-runner', image='gitlab/gitlab-runner:alpine',
	             main_path='/opt'):
		self.name = name
		self.gitlab_hostname = gitlab_hostname
		self.image = image
		self.path = os.path.join(main_path, 'gitlab-runner')
		# self.logs_path = os.path.join('/ver/run/docker.sock', '/var/run/docker.sock')
		self.network = network
		self.register_token = ''

	def add_service_to_compose(self, compose, gitlab_runner_name='gitlab-ce'):
		gitlab_runner = docker_compose.ComposeService(self.name, self.image)
		gitlab_runner.set_hostname(self.name)
		gitlab_runner.set_restart('always')
		gitlab_runner.set_container_name(self.name)
		gitlab_runner.add_depends_on(gitlab_runner_name)
		gitlab_runner.add_volume(self.path, '/etc/gitlab-runner')
		gitlab_runner.add_network(self.network)
		compose.add_service(gitlab_runner)

	def start_initialization(self, gitlab_api, run_type='docker'):
		group = gitlab_api.gitlab_api.groups.get(gitlab_api.group_id)
		self.register_token = group.runners_token
		if run_type == 'docker':
			command = f"docker exec {self.name} /bin/bash -c \"" \
			          f"gitlab-runner register --non-interactive --url {self.gitlab_hostname} " \
			          f"--registration-token {self.register_token} --executor \'docker\' " \
			          f"--docker-image alpine:latest --decription \'docker-runner\'" \
			          f"--tag-list \'docker\' --run-untagged=\'false\' --locked=\'false'\ --access-level=\'non_protected\'\""
			os.system(command)
