```bash
git clone
```
```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```
```bash
mkdir static && mkdir static/text static/audio static/report
mkdir llm/uploads whisper/whisperX-api/uploads utils/uploads
```
```bash
sudo apt install ffmpeg
```

```bash
sudo docker build whisper/whisperX-api -t whisper:latest
sudo docker build rabbitmq -t rabbit:castom
sudo docker run -d --rm --name postgres -p 127.0.0.1:5430:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:latest
sudo docker run --rm -d -p 127.0.0.1:5672:5672 -p 40002:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=admin --name rabbit rabbit:castom
sudo docker run -d --rm --name whisper --gpus 1 -p 127.0.0.1:5000:5000 whisper:latest
```
for last command there is need install NVIDIA docker drivers else --gpus will not work.

```bash
uvicorn gateaway.main:app --host 0.0.0.0 --port 40001
```

###within other windows:
- python main_agent.py
- python wisper_agent.py
- python llm_agent.py
- python sender_agent.py
- python utils/bot.py

###finally result global:
- 40001 - fastapi interface
- 40002 - rabbitmq managment with admin user admin:admin, if need update base admin, change rabbitmq/settings/definitions.json

###local:
- 5432 - postgres
- 5672 - rabbitmq queue default exchange
- 5000 - whipser api
- 5001 - llm api
- agent for main, whisper, llm and answer queue and working tg bot.
