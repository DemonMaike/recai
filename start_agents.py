import subprocess
import threading

# Список скриптов для запуска
scripts = [
    "python main_agent.py",
    "python whisper_agent.py",
    "python llm_agent.py",
    "python sender_agent.py",
    "python utils/bot.py"
]

# Запуск каждого скрипта как субпроцесс
processes = []
for script in scripts:
    process = subprocess.Popen(
        script,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(process)

# Функция для чтения и вывода логов
def log_output(process):
    for line in process.stdout:
        print(line, end='')
    for line in process.stderr:
        print(line, end='')

# Создание и запуск потоков для логов
threads = []
for process in processes:
    thread = threading.Thread(target=log_output, args=(process,))
    thread.start()
    threads.append(thread)
