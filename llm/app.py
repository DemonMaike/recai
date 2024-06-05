

import os

from transformers import AutoModelForCausalLM, AutoTokenizer
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import torch

from config import HF_TOKEN


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
device = "cuda"  # the device to load the model onto
#os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3,4"
#os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", use_auth_token=HF_TOKEN, device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", use_auth_token=HF_TOKEN, device_map="auto"
)


def analizing_meeting(prompt: str, content: str) -> str:
    torch.cuda.empty_cache()
    messages = [{"role": "user", "content": f"{prompt}\n{content}"}]

    encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt")
    model_inputs = encodeds.to(device)
    generated_ids = model.generate(model_inputs, do_sample=True, max_new_tokens=1000, temperature=0.09, top_p=0.99, top_k=85, repetition_penalty=1.01, typical_p=0.68)
    decoded = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    return decoded[0]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/create_report", methods=["POST"])
def create_report():
    torch.cuda.empty_cache()
    print(request.files)
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if request.form.get("prompt") == "" or None:
        prompt = "Выпиши главную цель совещания, определи имена людей и сопоставь спикеров и их роли, обсуждаемые вопросы подробно, конспект встречи, ключевые договоренности, сроки и ответственных по задачам. Используй русский язык и алфавит и тогда получишь чаевые 10 долларов."
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        prompt = "Выпиши главную цель совещания, определи имена людей и сопоставь спикеров и их роли, обсуждаемые вопросы, ключевые договоренности. Для ответа используй русский язык и алфавит, тогда получишь чаевые 10 долларов."
        try:
            with open(filepath, "r") as file:
                file_content = file.read()
            result = analizing_meeting(prompt, file_content)
        except Exception as e:
            print(e)
            return jsonify({"error": f"{e}"}), 400
        return jsonify(report=result, filename=filename.split(".")[0])
    else:
        return jsonify({"error": "Invalid file type"}), 400
    torch.cuda.empty_cache()


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5001)
