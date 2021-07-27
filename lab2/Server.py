import os
import socket
import GoBacktoN
import Host


class Server(object):
    def __init__(self, localAddress, remoteAddress=None):
        # 本地地址
        self.localAddress = localAddress
        # 目标地址
        self.remoteAddress = remoteAddress
        # 本地套接字
        self.localSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.localSocket.bind(localAddress)

    # 在得知目的地址后初始化目的地址
    def setRemote(self, address):
        self.remoteAddress = address


if __name__ == "__main__":
    print('客户端开始运行')
    # 初始化服务器端
    server = Server(Host.Host.address2)
    while True:
        # 接受client的请求和地址
        clientData, clientAddress = server.localSocket.recvfrom(1024)
        server.setRemote(clientAddress)
        clientData = clientData.decode()
        print(clientData)
        print('消息从:' + server.remoteAddress[0] + str(server.remoteAddress[1]) + '发来的')
        if 'DOWNLOAD' == clientData.upper():
            FileNames = []
            # 列出server文件夹中的全部文件名
            for i in os.listdir('ServerFile'):
                FileNames.append(i)
            FileNamesData = '|'.join(FileNames).encode(encoding='utf-8')
            server.localSocket.sendto(FileNamesData, server.remoteAddress)
            choiceFile = server.localSocket.recvfrom(1024)[0].decode()
            print('选择的文件名:', choiceFile)
            # 利用GBN协议传输
            serverSender = GoBacktoN.GBN(server.localAddress, server.remoteAddress, server.localSocket, 'ServerFile/' + choiceFile, 'ClientFile/' + choiceFile)
            serverSender.serverRun()
        elif 'UPLOAD' == clientData.upper():
            # 接受想要上传的文件名
            choiceFile = server.localSocket.recvfrom(1024)[0].decode()
            print('选择的文件名:', choiceFile)
            # 利用GBN协议传输
            serverSender = GoBacktoN.GBN(server.localAddress, server.remoteAddress, server.localSocket, 'ClientFile/' + choiceFile, 'ServerFile/' + choiceFile)
            serverSender.clientRun()
