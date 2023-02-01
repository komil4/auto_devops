import os
import uuid
import gitlab
import report
from docker import docker_compose


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


class Gitlab:
    def __init__(self, network, host='localhost', name='gitlab-ce', image='gitlab/gitlab-ce:latest',
                 http_port=1080, https_port=1443, ssh_port=1022, main_path='/opt', root_password='password'):
        self.name = name
        self.host = host
        self.gitlab_hostname = ''
        self.image = image
        self.http_port = http_port
        self.https_port = https_port
        self.ssh_port = ssh_port
        self.tls_on = False
        self.data_path = os.path.join(main_path, 'gitlab-ce/data')
        self.logs_path = os.path.join(main_path, 'gitlab-ce/logs')
        self.config_path = os.path.join(main_path, 'gitlab-ce/config')
        self.network = network
        self.root_password = root_password
        self.gitlab_api = None

    def add_service_to_compose(self, compose):
        gitlab_ce = docker_compose.ComposeService(self.name, self.image)
        gitlab_ce.set_restart('always')
        gitlab_ce.set_hostname(self.host)
        gitlab_ce.set_container_name(self.name)
        gitlab_ce.add_port(str(self.http_port), '1080')
        gitlab_ce.add_port(str(self.https_port), '1443')
        gitlab_ce.add_port(str(self.ssh_port), '22')
        gitlab_ce.add_volume(self.config_path, '/etc/gitlab')
        gitlab_ce.add_volume(self.data_path, '/var/opt/gitlab')
        gitlab_ce.add_volume(self.logs_path, '/var/log/gitlab')
        gitlab_ce.add_network(self.network)
        compose.add_service(gitlab_ce)
        report.report_progress("Add Gitlab to compose file")

    def start_initialization(self, tls_on=False):
        self.tls_on = tls_on
        self.gitlab_hostname = f'https://{self.host}:{self.https_port}' if tls_on else f'http://{self.host}:{self.http_port}'
        f_struct = {'external_url': self.gitlab_hostname}
        f_mask = get_find_mask_gitlab_rb(f_struct)
        f_value = get_value_gitlab_rb(f_struct)
        command = f"docker exec gitlab-ce /bin/bash -c \"sed -i \'s!{f_mask}!{f_value}!\' /etc/gitlab/gitlab.rb\""
        os.system(command)
        report.report_progress("Change Gitlab Url")

        f_struct = {'gitlab_rails': {'gitlab_shell_ssh_port': str(self.ssh_port)}}
        f_mask = get_find_mask_gitlab_rb(f_struct)
        f_value = get_value_gitlab_rb(f_struct)
        command = f"docker exec gitlab-ce /bin/bash -c \"sed -i \'s!{f_mask}!{f_value}!\' /etc/gitlab/gitlab.rb\""
        os.system(command)
        report.report_progress("Change Gitlab SSH port")

        os.system("docker exec gitlab-ce /bin/bash -c \"gitlab-ctl reconfigure;gitlab-ctl restart\"")
        report.report_progress("Restart Gitlab")

        gitlab_root = GitlabApi(self.gitlab_hostname)
        gitlab_root.generate_root_access_token()
        report.report_progress("Generate Gitlab access token")
        gitlab_root.set_root_password(self.root_password)
        report.report_progress("Generate Gitlab root password")
        gitlab_root.authenticate_gitlab()

        self.gitlab_api = gitlab_root


class GitlabApi:
    def __init__(self, external_url):
        self.external_url = external_url
        self.root_password = ''
        self.root_access_token = ''
        self.root_ssh_key = ''
        self.gitlab_api = None
        self.group_id = None
        self.project_id = None
        self.user_ids = []
        self.member_ids = []

    def set_root_password(self, password):
        command = "docker exec gitlab-ce /bin/bash -c \""\
                  "gitlab-rails runner \\\"user = User.find_by_username(\'root\'); " \
                  f"user.password = \'{password}\'; " \
                  f"user.password_confirmation = \'{password}\'; " \
                  "user.save!; exit!\\\"\""
        # print(command)
        os.system(command)
        self.root_password = password

    def generate_root_access_token(self):
        token = uuid.uuid4().hex
        command = "docker exec gitlab-ce /bin/bash -c \""\
                  f"gitlab-rails runner \\\"token = User.find_by_username(\'root\')" \
                  ".personal_access_tokens.create(scopes: [:api, :read_user, :read_repository, :write_repository, :sudo], name: \'Automation token\'); " \
                  f"token.set_token(\'{token}\'); " \
                  "token.save!; exit!\\\"\""
        # print(command)
        os.system(command)
        self.root_access_token = token

    def set_root_user_ssh_key(self, key):
        user = self.gitlab_api.user
        self.root_ssh_key = user.keys.create({'title': 'root',
                                              'key': key})

    def authenticate_gitlab(self):
        gitlab_api = gitlab.Gitlab(url=self.external_url, private_token=self.root_access_token)
        gitlab_api.auth()
        self.gitlab_api = gitlab_api

    def create_group(self, group_name, path):
        self.group_id = self.gitlab_api.groups.create({'name': group_name, 'path': path}).id

    def create_users(self, users_list):
        for user in users_list:
            self.user_ids.append(self.gitlab_api.users.create({'email': user.get('email'),
                                                               'password': user.get('password'),
                                                               'username': user.get('username'),
                                                               'name': user.get('name')}).id)

    def add_users_to_group_members(self, group_id=''):
        group = self.gitlab_api.groups.get(group_id if group_id != '' else self.group_id)
        for user_id in self.user_ids:
            group.members.create({'user_id': user_id,
                                  'access_level': gitlab.const.AccessLevel.GUEST})

    def create_project(self, project_name, path, group_id=''):
        self.project_id = self.gitlab_api.projects.create({'name': project_name, 'path': path,'namespace_id': group_id if group_id != '' else self.group_id}).id

    def set_project_variable(self, project_id, key, value, masked=False, protected=False):
        project = self.gitlab_api.projects.get(project_id)
        project.variables.create({'key': key, 'value': value, 'masked': masked, 'protected': protected})

