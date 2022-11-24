import os
import uuid


class Gitlab:
    def __init__(self, external_url, root_password):
        self.external_url = external_url
        self.root_password = root_password
        self.root_access_token = ''

    def generate_access_token(self, username):
        token = uuid.uuid4().hex
        command = f"sudo gitlab-rails runner \"token = User.find_by_username(\'{username}\')" \
                  ".personal_access_tokens.create(scopes: [:username], name: \'Automation token\'); " \
                  f"token.set_token(\'{token}\'); " \
                  "token.save!\""
        os.system(command)
        self.root_access_token = token

