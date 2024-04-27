git clone

python -m venv env
source env/bin/activate
pip install -r requirements.txt

sudo docker build whiper/wishperX-api -t whisper:latest
sudo docker build rabbitmq -t rabbit:castom
sudo docker run -d --rm --name postgres -p 127.0.0.1:5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSSWORD=postgres postgres:latest
sudo docker run -d --rm --name rabbit -p 40002:15672 -p 127.0.0.1:5672:5672 -e RABBIT_DEFAULT_USER=admin -e RABBIT_DEFAULT_PASSWORD=admin rabbit:castom
sudo docker run -d --rm --name whisper --gpus 1 -p 127.0.0.1:5000:5000 whisper:latest
for last command there is need install NVIDIA docker drivers else --gpus will not work.

uvicorn gateaway.main:app --host 0.0.0.0 --port 40001

within other windows:
python main_agent.py
python wisper_agent.py

finally result global:
40001 - fastapi interface
40002 - rabbitmq managment with admin user admin:admin, if need update base admin, change rabbitmq/settings/definitions.json

local:
5432 - postgres
5672 - rabbitmq queue default exchange
5000 - whipser api
agent for main and whisper clasters.
