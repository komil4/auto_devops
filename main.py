import os

import dockerCompose

network = dockerCompose.ComposeNetwork('gitlab', 'gitlab-network')

gitlab_ce = dockerCompose.ComposeService('gitlab-ce', 'gitlab/gitlab-ce:latest')
gitlab_ce.set_restart('always')
gitlab_ce.set_hostname('localhost')
gitlab_ce.set_container_name('gitlab-ce')
gitlab_ce.add_environment('GITLAB_OMNIBUS_CONFIG', {'external_url': 'http://localhost:10080',
                                                    'gitlab_rails[\'initial_root_password\']': 'root'})
gitlab_ce.add_port('10080', '10080')
gitlab_ce.add_port('10443', '10443')
gitlab_ce.add_network(network)

gitlab_runner = dockerCompose.ComposeService('gitlab-runner', 'gitlab/gitlab-runner:alpine')
gitlab_runner.set_restart('always')
gitlab_runner.set_container_name('gitlab-runner')
gitlab_runner.add_depends_on('web')
gitlab_runner.add_network(network)

postgres_db = dockerCompose.ComposeService('postgres_db', 'postgres:latest')
postgres_db.set_restart('unless-stopped')
postgres_db.set_container_name('postgres_db')
postgres_db.add_environment('POSTGRES_USER', 'admin')
postgres_db.add_environment('POSTGRES_PASSWORD', 'Admin123')
postgres_db.add_environment('POSTGRES_DB', 'sonarqube')
postgres_db.add_volume('../docker-postgresql-multiple-databases', '/docker-entrypoint-initdb.d')


sonarqube = dockerCompose.ComposeService('sonarqube', 'sonarqube:latest')
sonarqube.set_restart('unless-stopped')
sonarqube.set_container_name('sonarqube')
sonarqube.add_environment('SONARQUBE_JDBC_USERNAME', 'admin')
sonarqube.add_environment('SONARQUBE_JDBC_PASSWORD', 'admin')
sonarqube.add_environment('SONARQUBE_JDBC_URL', 'jdbc:postgresql://db:5432/sonarqube')
sonarqube.add_port('19000', '9000')
sonarqube.add_port('19092', '9092')

compose = dockerCompose.ComposeStruct()
compose.add_service(gitlab_ce)
compose.add_service(gitlab_runner)
compose.add_service(postgres_db)
compose.add_service(sonarqube)
compose.add_network(network)

compose.save_file(os.getcwd(), 'docker-compose')
