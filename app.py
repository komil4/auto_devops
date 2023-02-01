import os
from docker import pgadmin, postgres, gitlab_runner, gitlab_ce, sonar, docker_compose

compose = docker_compose.ComposeStruct()

network = docker_compose.ComposeNetwork('devops', 'devops-network')
compose.add_network(network)

gitlab_class = gitlab_ce.Gitlab(network, host='localhost', main_path='./dirs')
gitlab_runner_class = gitlab_runner.GitlabRunner(network, main_path='./dirs')

gitlab_class.add_service_to_compose(compose)
gitlab_runner_class.add_service_to_compose(compose)

postgres_class = postgres.Postgres(network, main_path='./dirs', database_names=['sonarqube', 'allure'])
postgres_class.add_service_to_compose(compose)

pgadmin_class = pgadmin.PgAdmin(network)
pgadmin_class.add_service_to_compose(compose)

sonar_class = sonar.SonarQube(network, main_path='./dirs')
sonar_class.add_service_to_compose(compose)

compose.save_file(os.getcwd(), 'docker-compose')

# SonarQube
sonar_class.start_initialization(gitlab_class.host, ['my_project'])

# GitLab
gitlab_class.start_initialization()

group_path = "my_group"
gitlab_class.gitlab_api.create_group("My group", group_path)
users = [{'email': 'mail1@mail.ru', 'password': 'password', 'username': 'first', 'name': 'First User'},
         {'email': 'mail2@mail.ru', 'password': 'password', 'username': 'second', 'name': 'Second User'}]
gitlab_class.gitlab_api.create_users(users)
gitlab_class.gitlab_api.add_users_to_group_members(gitlab_class.gitlab_api.group_id)
project_path = "my_project"
gitlab_class.gitlab_api.create_project("My project", project_path, gitlab_class.gitlab_api.group_id)

gitlab_class.gitlab_api.set_project_variable(gitlab_class.gitlab_api.project_id, 'SONAR_HOST_URL', f"http://{gitlab_class.host}:{sonar_class.port}")
gitlab_class.gitlab_api.set_project_variable(gitlab_class.gitlab_api.project_id, 'SONAR_TOKEN', sonar_class.access_token)

# GitlabRunner
gitlab_runner_class.start_initialization(gitlab_class)

# Sonar
# GR1348941yoBpzLbHE_K_wCU-J5F-


