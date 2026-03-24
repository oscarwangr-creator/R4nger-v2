import asyncio
import aio_pika  # For RabbitMQ
from typing import Callable, Any, Dict, Optional

class DistributedTaskManager:
    def __init__(self, queue: str, rabbitmq_url: str):
        self.queue = queue
        self.rabbitmq_url = rabbitmq_url

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

    async def disconnect(self) -> None:
        await self.connection.close()

    async def send_task(self, task: Dict[str, Any]) -> None:
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=str(task).encode()),
            routing_key=self.queue,
        )

    async def worker(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        await self.connect()
        async with self.channel:
            queue = await self.channel.get_queue(self.queue)
            async for message in queue:
                async with message.process():
                    task = eval(message.body.decode())
                    await callback(task)


# Example Callback Function
async def example_task_handler(task: Dict[str, Any]) -> None:
    print(f"Handling task: {task}")
    await asyncio.sleep(1)  # Simulate task processing

# Example Usage
if __name__ == '__main__':
    task_manager = DistributedTaskManager(queue='task_queue', rabbitmq_url='amqp://guest:guest@localhost/')
    asyncio.run(task_manager.worker(example_task_handler))
