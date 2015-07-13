## serveur ##

import ssl, socket, ip_addr

localhost = ip_addr.get_local_addr()
port = 30000

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind((localhost, port))
serv.listen(5)
client, addr = serv.accept()
tunnel = ssl.wrap_socket(client, server_side=True, keyfile="truc.key", certfile="truc.crt")

tunnel.send('truc en boite'.encode())

## client ##

import ssl, socket, ip_addr

remotehost = ip_addr.get_local_addr()
port = 30000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((remotehost, port))
tunnel, addr = ssl.wrap_socket(client)

tunnel.recv(1024).decode()