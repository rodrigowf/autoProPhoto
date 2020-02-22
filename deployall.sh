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

# Install Stackdriver logging agent
curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh
sudo bash install-logging-agent.sh

# Install or update needed software
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install -yq supervisor python3-pip
pip3 install --upgrade pip virtualenv

# Install development and runtime libraries (~4GB)
sudo apt-get install --no-install-recommends \
    cuda-10-1 \
    libcudnn7=7.6.4.38-1+cuda10.1  \
    libcudnn7-dev=7.6.4.38-1+cuda10.1


# Install TensorRT. Requires that libcudnn7 is installed above.
sudo apt-get install -y --no-install-recommends libnvinfer6=6.0.1-1+cuda10.1 \
    libnvinfer-dev=6.0.1-1+cuda10.1 \
    libnvinfer-plugin6=6.0.1-1+cuda10.1

# END CUDA -----------------------------------


# Account to own server process
sudo useradd -m -d /home/refotoapp refotoapp

# Fetch source code
export HOME=/root
sudo git clone https://github.com/rodrigowf/autoProPhoto.git /opt/app

sudo chmod -R 777 /opt/app

# Python environment setup
python3 -m virtualenv -p python3 /opt/app/env
sudo chmod -R 777 /opt/app
source /opt/app/env/bin/activate
/opt/app/env/bin/pip install -r /opt/app/requirements.txt


# Set ownership to newly created account
sudo chown -R refotoapp:refotoapp /opt/app
sudo chmod -R 754 /opt/app

# Put supervisor configuration in proper place
sudo cp /opt/app/refoto.conf /etc/supervisor/conf.d/refoto.conf

# Start service via supervisorctl
sudo supervisorctl reread
sudo supervisorctl update