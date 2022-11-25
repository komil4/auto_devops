import os
import gitlab_ce
import docker_compose
import requests


def get_find_mask_gitlab_rb(prop):
    mask = '.*'
    if isinstance(prop, dict):
        for prop_name in prop:
            value = prop[prop_name]
            if isinstance(value, dict):
                for value_name in value:
                    mask = f'{mask}{prop_name}..{value_name}'
            else:
                mask = f'{mask}{prop_name}'
    else:
        mask = f'{mask}{prop}'
    mask = f'{mask}.*[=\\x27].*'

    return mask


def get_value_gitlab_rb(prop):
    new_value = ' '
    if isinstance(prop, dict):
        for prop_name in prop:
            value = prop[prop_name]
            if isinstance(value, dict):
                for value_name in value:
                    value_str = f"\\x27{value[value_name]}\\x27" if isinstance(value[value_name], str) \
                        else f"{value[value_name]}"
                    new_value = f"{new_value}{prop_name}[\\x27{value_name}\\x27] = {value_str}"
            else:
                value_str = f"\\x27{value}\\x27" if isinstance(value, str) \
                    else f"{value}"
                new_value = f"{new_value}{prop_name} {value_str}"
    else:
        new_value = f'{new_value}'

    return new_value

gitlab_host = 'http://localhost'
gitlab_port = '1080'
gitlab_hostname = f"{gitlab_host}:{gitlab_port}" if gitlab_port != '' else gitlab_host
# min 8 characters
gitlab_root_password = 'password'
gitlab_shell_ssh_port = 1022

gitlab_root = gitlab_ce.Gitlab(gitlab_hostname)

# Compose part

network = docker_compose.ComposeNetwork('devops', 'devops-network')

gitlab_ce = docker_compose.ComposeService('gitlab-ce', 'gitlab/gitlab-ce:latest')
gitlab_ce.set_restart('always')
gitlab_ce.set_hostname('localhost')
gitlab_ce.set_container_name('gitlab-ce')
gitlab_ce.add_port('1080', '1080')
gitlab_ce.add_port('1443', '1443')
gitlab_ce.add_port('1022', '22')
gitlab_ce.add_volume('./config', '/etc/gitlab')
gitlab_ce.add_network(network)

gitlab_runner = docker_compose.ComposeService('gitlab-runner', 'gitlab/gitlab-runner:alpine')
gitlab_runner.set_restart('always')
gitlab_runner.set_hostname('gitlab-runner')
gitlab_runner.set_container_name('gitlab-runner')
gitlab_runner.add_depends_on('gitlab-ce')
gitlab_runner.add_network(network)

postgres_db = docker_compose.ComposeService('postgres_db', 'postgres:latest')
postgres_db.set_restart('unless-stopped')
postgres_db.set_hostname('postgres_db')
postgres_db.set_container_name('postgres_db')
postgres_db.add_environment('POSTGRES_USER', 'admin')
postgres_db.add_environment('POSTGRES_PASSWORD', 'Admin123')
postgres_db.add_environment('POSTGRES_MULTIPLE_DATABASES', 'sonarqube:admin,allure:admin')
postgres_db.add_volume('./docker-postgresql-multiple-databases', '/docker-entrypoint-initdb.d')
postgres_db.add_network(network)

sonarqube = docker_compose.ComposeService('sonarqube', 'sonarqube:latest')
sonarqube.set_restart('unless-stopped')
sonarqube.set_hostname('sonarqube')
sonarqube.set_container_name('sonarqube')
sonarqube.add_environment('SONARQUBE_JDBC_USERNAME', 'sonarqube')
sonarqube.add_environment('SONARQUBE_JDBC_PASSWORD', 'admin')
sonarqube.add_environment('SONARQUBE_JDBC_URL', 'jdbc:postgresql://postgres_db:5432/sonarqube')
'''
sonarqube.add_environment('SONAR_SEARCH_JAVAOPTS', '-Xmx2G -Xms2G -XX:MaxDirectMemorySize=1G -XX:+HeapDumpOnOutOfMemoryError')
sonarqube.add_environment('SONAR_CE_JAVAOPTS', '-Xmx2G -Xms128m -XX:+HeapDumpOnOutOfMemoryError')
sonarqube.add_environment('SONAR_WEB_JAVAOPTS', '-Xmx1G -Xms128m -XX:+HeapDumpOnOutOfMemoryError')
'''
sonarqube.add_port('19000', '9000')
sonarqube.add_port('19092', '9092')
sonarqube.add_network(network)
sonarqube.add_deploy('resources', {'limits': {'cpus': '2', 'memory': '1500M'}})

pgadmin = docker_compose.ComposeService('pgadmin', 'dpage/pgadmin4:latest')
pgadmin.set_restart('always')
pgadmin.set_container_name('pgadmin')
pgadmin.add_environment('PGADMIN_DEFAULT_EMAIL', 'raj@nola.com')
pgadmin.add_environment('PGADMIN_DEFAULT_PASSWORD', 'admin')
pgadmin.add_port('2080', '80')
pgadmin.add_network(network)

compose = docker_compose.ComposeStruct()
compose.add_service(gitlab_ce)
compose.add_service(gitlab_runner)
compose.add_service(postgres_db)
compose.add_service(sonarqube)
compose.add_service(pgadmin)
compose.add_network(network)

compose.save_file(os.getcwd(), 'docker-compose')

f_struct = {'external_url': gitlab_hostname}
f_mask = get_find_mask_gitlab_rb(f_struct)
f_value = get_value_gitlab_rb(f_struct)
command = f"docker exec gitlab-ce /bin/bash -c \"sed -i \'s!{f_mask}!{f_value}!\' /etc/gitlab/gitlab.rb\""
os.system(command)

f_struct = {'gitlab_rails': {'gitlab_shell_ssh_port': gitlab_shell_ssh_port}}
f_mask = get_find_mask_gitlab_rb(f_struct)
f_value = get_value_gitlab_rb(f_struct)
command = f"docker exec gitlab-ce /bin/bash -c \"sed -i \'s!{f_mask}!{f_value}!\' /etc/gitlab/gitlab.rb\""
os.system(command)
'''
# print(command)
os.system(command)

f_struct = {'gitlab_rails': {'initial_root_password': gitlab_root_password}}
f_mask = get_find_mask_gitlab_rb(f_struct)
f_value = get_value_gitlab_rb(f_struct)
command = f"docker exec gitlab-ce /bin/bash -c \"sed -i \'s!{f_mask}!{f_value}!\' /etc/gitlab/gitlab.rb\""

# gitlab_rails['initial_root_password']
# print(command)
os.system(command)
'''
os.system("docker exec gitlab-ce /bin/bash -c \"gitlab-ctl reconfigure;gitlab-ctl restart\"")


# GitLab
gitlab_root.generate_root_access_token()
gitlab_root.set_root_password(gitlab_root_password)
gitlab_root.authenticate_gitlab()

group_path = "my_group"
gitlab_root.create_group("My group", group_path)
users = [{'email': 'mail1@mail.ru', 'password': 'password', 'username': 'first', 'name': 'First User'},
         {'email': 'mail2@mail.ru', 'password': 'password', 'username': 'second', 'name': 'Second User'}]
gitlab_root.create_users(users)
gitlab_root.add_users_to_group_members(gitlab_root.group_id)
project_path = "my_project"
gitlab_root.create_project("My project", project_path, gitlab_root.group_id)


# Oscript
repo_hostname = gitlab_host.replace('http://', '')
repo_hostname = gitlab_host.replace('https://', '')
repo_hostname = f"{repo_hostname}:{gitlab_shell_ssh_port}"

repo_url = f"ssh://git@{repo_hostname}/{group_path}/{project_path}.git"

url = 'http://localhost:5000/settings/SaveSettingsAndGetSsh'
data = {'Dir': "D:\\1c_bases\\Хранилище", 'Url': repo_url, 'User': 'Администратор', 'Password': '123',
        'PrivateToken': gitlab_root.root_access_token, 'SSHkey': '', 'Hostname': gitlab_hostname}
response = requests.post(url, json=data)
response_struct = response.json()
ssh_key = response_struct.get('SSHkey')

gitlab_root.set_root_user_ssh_key(ssh_key)


