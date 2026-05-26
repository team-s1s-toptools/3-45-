# client.py
import socket
import ssl
import threading
import select
import struct

SERVER_HOST = "твой-сервер.onrender.com"  # ЗАМЕНИ НА СВОЙ ХОСТ!
SERVER_PORT = 443
SOCKS_PORT = 1080

def create_outer_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def handle_socks(client):
    try:
        data = client.recv(262)
        if not data or data[0] != 0x05:
            client.close()
            return
        client.send(b'\x05\x00')
        
        data = client.recv(262)
        if len(data) < 10 or data[1] != 0x01:
            client.close()
            return
        
        atype = data[3]
        if atype == 0x01:  # IPv4
            host = socket.inet_ntoa(data[4:8])
            port = struct.unpack('>H', data[8:10])[0]
        elif atype == 0x03:  # Domain
            host_len = data[4]
            host = data[5:5+host_len].decode()
            port = struct.unpack('>H', data[5+host_len:7+host_len])[0]
        else:
            client.close()
            return
        
        print(f"[SOCKS] {host}:{port}")
        
        # Внешний TLS без SNI
        outer = socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=10)
        outer_ctx = create_outer_context()
        outer_tls = outer_ctx.wrap_socket(outer, server_hostname=None)
        
        # Внутренний TLS с реальным SNI
        inner_ctx = ssl.create_default_context()
        inner_ctx.check_hostname = False
        inner_ctx.verify_mode = ssl.CERT_NONE
        inner_tls = inner_ctx.wrap_socket(outer_tls, server_hostname=host)
        
        client.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        
        client.setblocking(False)
        inner_tls.setblocking(False)
        
        while True:
            rlist, _, _ = select.select([client, inner_tls], [], [], 60)
            for sock in rlist:
                try:
                    data = sock.recv(8192)
                    if not data:
                        return
                    if sock is client:
                        inner_tls.send(data)
                    else:
                        client.send(data)
                except:
                    return
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            client.close()
        except:
            pass

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', SOCKS_PORT))
    srv.listen(100)
    print(f"SOCKS5 on 127.0.0.1:{SOCKS_PORT} -> {SERVER_HOST}:{SERVER_PORT}")
    
    while True:
        client, addr = srv.accept()
        print(f"[+] {addr[0]}")
        threading.Thread(target=handle_socks, args=(client,), daemon=True).start()

if __name__ == '__main__':
    main()