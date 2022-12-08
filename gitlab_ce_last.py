import os
import uuid
import gitlab_ce


class Gitlab:
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
        print(command)
        os.system(command)
        self.root_password = password

    def generate_root_access_token(self):
        token = uuid.uuid4().hex
        command = "docker exec gitlab-ce /bin/bash -c \""\
                  f"gitlab-rails runner \\\"token = User.find_by_username(\'root\')" \
                  ".personal_access_tokens.create(scopes: [:api, :read_user, :read_repository, :write_repository, :sudo], name: \'Automation token\'); " \
                  f"token.set_token(\'{token}\'); " \
                  "token.save!; exit!\\\"\""
        print(command)
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
