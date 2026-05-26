#!/usr/bin/env python3
import socket
import threading
import sys

def safe_send(sock, data):
    if not data or sock is None:
        return
    try:
        sock.send(data)
    except (BrokenPipeError, ConnectionResetError, OSError, AttributeError):
        pass

def get_target(data):
    try:
        lines = data.split(b'\r\n')
        for line in lines:
            if line.lower().startswith(b'host:'):
                host = line.split(b':', 1)[1].strip().decode()
                if ':' in host:
                    return host.split(':')[0], int(host.split(':')[1])
                return host, 80
    except:
        pass
    return 'example.com', 80

def handle_client(client_sock, addr):
    try:
        client_sock.settimeout(5.0)
        full_request = b''
        while True:
            chunk = client_sock.recv(4096)
            if not chunk:
                break
            full_request += chunk
            if len(chunk) < 4096:
                break
    except:
        client_sock.close()
        return
    
    if not full_request:
        client_sock.close()
        return
    
    target_host, target_port = get_target(full_request)
    
    try:
        target = socket.create_connection((target_host, target_port), timeout=10)
    except:
        safe_send(client_sock, b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
        client_sock.close()
        return
    
    try:
        target.send(full_request)
        target.settimeout(10.0)
        while True:
            chunk = target.recv(8192)
            if not chunk:
                break
            safe_send(client_sock, chunk)
    except:
        pass
    finally:
        target.close()
        client_sock.close()

def main():
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(100)
    print(f"Прокси на 0.0.0.0:{PORT} (динамический)", flush=True)
    
    while True:
        try:
            client, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client, addr))
            t.daemon = True
            t.start()
        except KeyboardInterrupt:
            break
    server.close()

if __name__ == '__main__':
    main()
