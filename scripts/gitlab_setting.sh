#!/bin/bash
docker exec -it gitlab-ctl /bin/bash
sed -i 's/\x23 external_url \x27GENERATED_EXTERNAL_URL\x27/ external_url \x27localhost:1080\x27/' /etc/gitlab/gitlab.rb
gitlab-ctl reconfigure