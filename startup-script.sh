# Copyright 2019 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Echo commands
set -v

# [START refoto_startup_script]
# Install Stackdriver logging agent
curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh
sudo bash install-logging-agent.sh

# Install or update needed software
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install -yq supervisor python3-pip
pip install --upgrade pip virtualenv

# Account to own server process
sudo useradd -m -d /home/refotoapp refotoapp

# Fetch source code
export HOME=/root
git clone https://github.com/rodrigowf/autoProPhoto.git /opt/app

# Python environment setup
virtualenv -p python3 /opt/app/env
source /opt/app/env/bin/activate
/opt/app/env/bin/pip install -r /opt/app/requirements.txt

# Set ownership to newly created account
sudo chown -R refotoapp:refotoapp /opt/app

# Put supervisor configuration in proper place
sudo cp /opt/app/refoto.conf /etc/supervisor/conf.d/refoto.conf

# Start service via supervisorctl
sudo supervisorctl reread
sudo supervisorctl update
# [END refoto_startup_script]