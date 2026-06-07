import json
import logging
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import NoBrokersAvailable

logger = logging.getLogger(__name__)

class WineKafkaProducer:
    def __init__(self, broker: str, topic: str, num_partitions: int = 3, replication_factor: int = 1):
        self.broker = broker
        self.topic = topic
        self.num_partitions = num_partitions
        self.replication_factor = replication_factor
        self.producer = None

    def connect(self):
        """Проверяет существование топика и инициализирует продюсер."""
        try:
            self._ensure_topic_exists()
            self.producer = KafkaProducer(
                bootstrap_servers=[self.broker],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info(f"Kafka Producer успешно запущен для топика '{self.topic}'")
        except NoBrokersAvailable as e:
            logger.error(f"Брокер Kafka недоступен по адресу {self.broker}: {e}")
            self.producer = None
        except Exception as e:
            logger.error(f"Ошибка инициализации Kafka: {e}")
            self.producer = None

    def _ensure_topic_exists(self):
        """Создает топик с заданным числом партиций, если он отсутствует."""
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=[self.broker],
                client_id='wine_admin'
            )
            existing_topics = admin_client.list_topics()
            if self.topic not in existing_topics:
                logger.info(f"Создание топика '{self.topic}' с {self.num_partitions} партициями...")
                new_topic = NewTopic(
                    name=self.topic,
                    num_partitions=self.num_partitions,
                    replication_factor=self.replication_factor
                )
                admin_client.create_topics(new_topics=[new_topic], validate_only=False)
                logger.info(f"Топик '{self.topic}' успешно создан.")
            else:
                logger.info(f"Топик '{self.topic}' уже существует.")
            admin_client.close()
        except Exception as e:
            logger.warning(f"Не удалось проверить/создать топик через Admin API: {e}")

    def send_prediction(self, features: dict, result: dict):
        if not self.producer:
            logger.warning("Отправка отменена: Kafka Producer не подключен.")
            return
        message = {
            "features": features,
            "result": result
        }
        self.producer.send(self.topic, message)
        logger.info(f"Сообщение отправлено в топик '{self.topic}'")

    def close(self):
        if self.producer:
            self.producer.close()
            logger.info("Соединение с Kafka Producer закрыто")