FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Install the required packages
COPY environment.yaml /app
RUN apt update && apt install -y ffmpeg
RUN conda env create -f /app/environment.yaml

# Copy the app itself
RUN mkdir -p /app/uploads
COPY app.py config.py /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask to run on 0.0.0.0
ENV FLASK_RUN_HOST=0.0.0.0

# Run the command to start your app
CMD ["/opt/conda/envs/whisperx/bin/gunicorn", "-b", "0.0.0.0:5000", "--workers", "1", "--timeout", "500", "app:app"]
