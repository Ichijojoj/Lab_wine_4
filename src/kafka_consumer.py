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


class WineKafkaConsumer:
    def __init__(self, broker: str, topic: str, group_id: str = 'wine_consumer_group'):
        self.broker = broker
        self.topic = topic
        self.group_id = group_id
        self.consumer = None
        self.db = OracleDB()

    def wait_for_kafka(self, retries=10, delay=5):
        for i in range(retries):
            try:
                temp_consumer = KafkaConsumer(bootstrap_servers=[self.broker])
                temp_consumer.close()
                logger.info("✅ Успешное подключение к Kafka!")
                return True
            except NoBrokersAvailable:
                logger.warning(f"⏳ Ожидание Kafka ({i + 1}/{retries})...")
                time.sleep(delay)
        raise Exception("Ошибка подключения к Kafka: брокер недоступен.")

    def start(self):
        self.wait_for_kafka()
        self.db.init_db()

        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=[self.broker],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=self.group_id,
            auto_offset_reset='earliest'
        )

        logger.info(f"🎧 Consumer запущен и ожидает сообщения в топике '{self.topic}'...")

        try:
            for message in self.consumer:
                data = message.value
                logger.info(f"📥 Получено сообщение из Kafka: {data}")

                features = data.get("features")
                result = data.get("result")

                if features and result:
                    self.db.save_prediction(features, result)
                    logger.info("💾 Данные успешно сохранены в БД Oracle")
        except KeyboardInterrupt:
            logger.info("Принудительная остановка консьюмера.")
        finally:
            self.close()

    def close(self):
        if self.consumer:
            self.consumer.close()
            logger.info("👋 Соединение с Kafka Consumer закрыто.")


if __name__ == "__main__":
    kafka_broker = os.getenv('KAFKA_BROKER', 'kafka:29092')
    kafka_topic = os.getenv('KAFKA_TOPIC', 'wine_predictions')

    consumer = WineKafkaConsumer(broker=kafka_broker, topic=kafka_topic)
    consumer.start()