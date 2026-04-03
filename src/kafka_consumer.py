import json
import os
import time
import logging
from kafka import KafkaConsumer
import sys
from kafka.errors import NoBrokersAvailable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.vault_manager import vault_manager
from database import OracleDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_kafka(broker, retries=10, delay=5):
    for i in range(retries):
        try:
            consumer = KafkaConsumer(bootstrap_servers=[broker])
            consumer.close()
            logger.info("Успешное подключение к Kafka!")
            return True
        except NoBrokersAvailable:
            logger.warning(f"⏳ Ожидание Kafka ({i + 1}/{retries})...")
            time.sleep(delay)
    raise Exception("Ошибка подключения к Kafka: брокер недоступен.")


def start_consumer():
    kafka_broker = os.getenv('KAFKA_BROKER', 'kafka:29092')
    wait_for_kafka(kafka_broker)

    db = OracleDB()
    db.init_db()

    consumer = KafkaConsumer(
        'wine_predictions',
        bootstrap_servers=[kafka_broker],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='wine_consumer_group',
        auto_offset_reset='earliest'
    )

    logger.info("🎧 Consumer запущен и ожидает сообщения...")

    for message in consumer:
        data = message.value
        logger.info(f"📥 Получено сообщение из Kafka: {data}")

        features = data.get("features")
        result = data.get("result")

        if features and result:
            db.save_prediction(features, result)
            logger.info("💾 Данные успешно сохранены в БД Oracle")


if __name__ == "__main__":
    start_consumer()