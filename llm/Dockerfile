FROM nvidia/cuda:11.8-base
RUN apt-get update && apt-get install -y wget bzip2 ca-certificates \
  libglib2.0-0 libxext6 libsm6 libxrender1 \
  git mercurial subversion

# Установка Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
RUN bash ~/miniconda.sh -b -p /opt/conda
RUN rm ~/miniconda.sh
ENV PATH="/opt/conda/bin:$PATH"
RUN conda update -n base -c defaults conda

WORKDIR /app

COPY environment.yaml /app
RUN conda env create -f /app/environment.yaml

ARG hftoken

# Copy the app itself
RUN mkdir -p /app/uploads
COPY app.py config.py ./

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variable for Flask to run on 0.0.0.0
ENV FLASK_RUN_HOST=0.0.0.0

# Run the command to start your app
CMD ["/opt/conda/envs/mistral/bin/gunicorn", "-b", "0.0.0.0:5001", "--workers", "1", "--timeout", "500", "app:app"]
