#!/usr/bin/env python3
import socket
import threading
import time

def safe_send(sock, data):
    if not data or sock is None:
        return
    try:
        sock.send(data)
    except (BrokenPipeError, ConnectionResetError, OSError, AttributeError):
        pass

def handle_client(client_sock, addr, target_host, target_port):
    try:
        target = socket.create_connection((target_host, target_port), timeout=10)
    except Exception:
        safe_send(client_sock, b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        client_sock.close()
        return

    try:
        # Принимаем данные от клиента
        first_chunk = b''
        second_chunk = b''
        
        client_sock.settimeout(5.0)
        try:
            first_chunk = client_sock.recv(500)
            second_chunk = client_sock.recv(4096)
        except socket.timeout:
            pass
        
        # Склеиваем и отправляем цели
        full_request = first_chunk + second_chunk
        if full_request:
            target.send(full_request)
        
        # Получаем ответ
        response = b''
        while True:
            try:
                chunk = target.recv(8192)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break
            except:
                break
        
        target.close()
        
        if not response:
            client_sock.close()
            return
        
        # Разделяем ответ на две части
        mid = len(response) // 2
        
        # Отправляем с защитой от разрыва
        safe_send(client_sock, response[:mid])
        time.sleep(0.3)  # задержка между частями
        safe_send(client_sock, response[mid:])
        
    except Exception:
        pass
    finally:
        try:
            client_sock.close()
        except:
            pass

def main():
    HOST = '0.0.0.0'
    PORT = 8888
    TARGET_HOST = 'example.com'  # поменяй на нужный
    TARGET_PORT = 80
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(100)
    print(f"Прокси на {HOST}:{PORT} -> {TARGET_HOST}:{TARGET_PORT}")
    
    while True:
        try:
            client, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client, addr, TARGET_HOST, TARGET_PORT))
            t.daemon = True
            t.start()
        except KeyboardInterrupt:
            break
        except:
            continue
    
    server.close()

if __name__ == '__main__':
    main()
