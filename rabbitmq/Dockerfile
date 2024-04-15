FROM rabbitmq:3.13-management

RUN mkdir -p /etc/rabbitmq

COPY settings/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY settings/definitions.json /settings/definitions.json

ENV RABBITMQ_CONF_FILE=/etc/rabbitmq/rabbitmq.conf

EXPOSE 5672 15672
