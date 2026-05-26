# server.py
import socket
import ssl
import threading
import struct
import sys

def create_ssl_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    context.set_servername_callback(None)
    return context

def parse_sni(data):
    try:
        if len(data) < 43 or data[0] != 0x16 or data[5] != 0x01:
            return None
        pos = 43
        while pos + 4 < len(data):
            ext_type = struct.unpack('>H', data[pos:pos+2])[0]
            ext_len = struct.unpack('>H', data[pos+2:pos+4])[0]
            if ext_type == 0x0000:
                sni_len = struct.unpack('>H', data[pos+6:pos+8])[0]
                return data[pos+8:pos+8+sni_len].decode()
            pos += 4 + ext_len
    except:
        pass
    return None

def handle_client(outer, addr):
    try:
        outer.settimeout(10)
        inner_hello = outer.recv(4096)
        if not inner_hello:
            outer.close()
            return
        
        target_host = parse_sni(inner_hello)
        if not target_host:
            outer.close()
            return
        
        print(f"[{addr[0]}] -> {target_host}")
        target = socket.create_connection((target_host, 443), timeout=10)
        target.send(inner_hello)
        
        outer.setblocking(False)
        target.setblocking(False)
        
        while True:
            rlist, _, _ = select.select([outer, target], [], [], 60)
            for sock in rlist:
                try:
                    data = sock.recv(8192)
                    if not data:
                        return
                    if sock is outer:
                        target.send(data)
                    else:
                        outer.send(data)
                except:
                    return
    except Exception as e:
        print(f"[{addr[0]}] error: {e}")
    finally:
        try:
            outer.close()
        except:
            pass

def main():
    import select
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 443))
    server.listen(100)
    
    ctx = create_ssl_context()
    print("TLS-in-TLS server on :443")
    
    while True:
        client, addr = server.accept()
        tls = ctx.wrap_socket(client, server_side=True, do_handshake_on_connect=False)
        try:
            tls.do_handshake()
        except:
            tls.close()
            continue
        threading.Thread(target=handle_client, args=(tls, addr), daemon=True).start()

if __name__ == '__main__':
    main()
