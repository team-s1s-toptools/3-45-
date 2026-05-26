import socket
import threading
from queue import Queue

def handle_client(client_sock, target_host, target_port):
    # Подключаемся к цели
    target = socket.create_connection((target_host, target_port))
    
    # Очереди для буферизации
    to_target = Queue()
    to_client = Queue()
    
    def reader(src, dst_queue, dst_sock=None):
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst_queue.put(data)
            if dst_sock:
                # Вторая часть — отложенная отправка
                pass
        dst_queue.put(None)
    
    def writer(src_queue, dst_sock, delay=0):
        while True:
            data = src_queue.get()
            if data is None:
                break
            # Имитация раздельной обработки — задержка между частями
            if delay:
                threading.Event().wait(delay)
            dst_sock.send(data)
    
    # Читаем от клиента, делим на 2 части
    first_part = client_sock.recv(2048)  # Первая половина
    second_part = client_sock.recv(2048) # Вторая половина
    
    # Обрабатываем отдельно
    processed_first = first_part.upper()  # Твоя логика
    processed_second = second_part.lower()
    
    # Склеиваем и отправляем цели
    target.send(processed_first + processed_second)
    
    # Ответ от цели — тоже разделяем
    resp = target.recv(4096)
    mid = len(resp)//2
    client_sock.send(resp[:mid])
    threading.Event().wait(0.5)  # разрыв
    client_sock.send(resp[mid:])
    
    target.close()
    client_sock.close()

# Запуск
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('0.0.0.0', 8888))
sock.listen(50)

while True:
    client, addr = sock.accept()
    t = threading.Thread(target=handle_client, args=(client, 'example.com', 80))
    t.start()
