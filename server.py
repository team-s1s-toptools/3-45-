#!/usr/bin/env python3
import socket
import threading
import time
import sys

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
    except Exception as e:
        safe_send(client_sock, b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        client_sock.close()
        return

    try:
        client_sock.settimeout(5.0)
        full_request = b''
        try:
            while True:
                chunk = client_sock.recv(4096)
                if not chunk:
                    break
                full_request += chunk
                if len(chunk) < 4096:
                    break
        except socket.timeout:
            pass
        except:
            pass
        
        if full_request:
            target.send(full_request)
        
        # Получаем ответ целиком
        response = b''
        target.settimeout(10.0)
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
        
        # *** ГЛАВНОЕ: отправляем ВЕСЬ ответ целиком, без разделения ***
        # Render не любит задержки между частями ответа
        safe_send(client_sock, response)
        
    except Exception as e:
        pass
    finally:
        try:
            client_sock.close()
        except:
            pass

def main():
    HOST = '0.0.0.0'
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    TARGET_HOST = 'example.com'  # ЗАМЕНИ НА СВОЙ
    TARGET_PORT = 80
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(100)
    print(f"Прокси на {HOST}:{PORT} -> {TARGET_HOST}:{TARGET_PORT}", flush=True)
    
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
