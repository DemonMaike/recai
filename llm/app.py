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

model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", use_auth_token=HF_TOKEN
)
tokenizer = AutoTokenizer.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", use_auth_token=HF_TOKEN
)
model = model.to(device)
model = torch.nn.DataParallel(model)


def analizing_meeting(prompt: str, diarization: str) -> str:
    messages = [{"role": "user", "content": f"{prompt}\n{diarization}"}]

    encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt")
    model_inputs = encodeds.to(device)

    generated_ids = model.generate(model_inputs, max_new_tokens=1000, do_sample=True)
    decoded = tokenizer.batch_decode(generated_ids)

    return decoded[0]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/create_report", methods=["POST"])
def create_report():
    print(request.files)
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if request.form.get("prompt") == "" or None:
        return jsonify({"error": "No prompt"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        prompt = request.form.get("prompt")
        try:
            result = analizing_meeting(prompt, filepath)
        except Exception as e:
            return jsonify({"error": f"{e}"}), 400
        return jsonify(report=result, filename=file.filename.split(".")[0])
    else:
        return jsonify({"error": "Invalid file type"}), 400


if __name__ == "__main__":
    app.run(debug=True)
