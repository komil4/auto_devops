import gitlab_runner
import gitlab_ce
import docker_compose
import os
import postgres
import sonar

compose = docker_compose.ComposeStruct()

network = docker_compose.ComposeNetwork('devops', 'devops-network')
compose.add_network(network)

gitlab_class = gitlab_ce.Gitlab(network, host='localhost', main_path='./dirs')
gitlab_runner_class = gitlab_runner.GitlabRunner(network, f"{gitlab_class.gitlab_hostname}:{gitlab_class.http_port}", main_path='./dirs')

gitlab_class.add_service_to_compose(compose)
gitlab_runner_class.add_service_to_compose(compose)

postgres_class = postgres.Postgres(network, database_names=['sonarqube', 'allure'])
postgres_class.add_service_to_compose(compose)

sonar_class = sonar.SonarQube(network)
sonar_class.add_service_to_compose(compose)

compose.save_file(os.getcwd(), 'docker-compose')

# GitLab
gitlab_class.start_initialization()
gitlab_class.gitlab_api.generate_root_access_token()
gitlab_class.gitlab_api.set_root_password()
gitlab_class.gitlab_api.authenticate_gitlab()

group_path = "my_group"
gitlab_class.gitlab_api.create_group("My group", group_path)
users = [{'email': 'mail1@mail.ru', 'password': 'password', 'username': 'first', 'name': 'First User'},
         {'email': 'mail2@mail.ru', 'password': 'password', 'username': 'second', 'name': 'Second User'}]
gitlab_class.gitlab_api.create_users(users)
gitlab_class.gitlab_api.add_users_to_group_members(gitlab_class.gitlab_api.group_id)
project_path = "my_project"
gitlab_class.gitlab_api.create_project("My project", project_path, gitlab_class.gitlab_api.group_id)

# GitlabRunner
gitlab_runner_class.start_initialization(gitlab_class.gitlab_api)

# Sonar


