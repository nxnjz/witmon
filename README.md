## About

I wrote this to monitor hosts/services on my internal network, which is behind double NAT. It's very rudimentary but works well. 

## Installation

Install dependencies and clone the repo. 

```
pip3 install pyaml
git clone https://gitlab.com/nxnjz/witmon.git
```


## Setup

* Create a telegram bot via https://t.me/BotFather
* Rename `config.yaml.example` to `config.yaml`
* Set your bot access token in `config.yaml`
* Start a chat with your bot. 
* Run `python3 witmon.py init`, and find your chat_id
* Set the chat_id in `config.yaml`
* Run `python3 witmon.py`

## Systemd

To use as a systemd service:

* Place the witmon directory under `/opt/`. 
* `cp /opt/witmon/witmon.service /etc/systemd/system/`
* `systemctl daemon-reload`
* To enable at boot and start immediately, use `systemctl enable --now witmon.service`.

## Note

Main repo is on gitlab, it is mirrored to github which may not always be up to date. 

https://gitlab.com/nxnjz/witmon

