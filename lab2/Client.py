import GoBacktoN
import Host
import os
import socket


class Client(object):
    def __init__(self, localAddress, remoteAddress):
        # 本地地址
        self.localAddress = localAddress
        # 目标地址
        self.remoteAddress = remoteAddress
        # 创建本地套接字
        self.localSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.localSocket.bind(localAddress)


if __name__ == "__main__":
    # 初始化客户端
    client = Client(Host.Host.address1, Host.Host.address2)
    while True:
        print('上传文件(UPLOAD)还是下载文件(DOWNLOAD)?')
        choice = input('请输入:')
        print('你的选择是', choice)
        if choice.upper() == 'UPLOAD':
            fileName = []
            # 获取上传文件夹的全部文件名
            for i in os.listdir('ClientFile'):
                fileName.append(i)
            print('请从下面文件中选择一个:')
            for i in range(len(fileName)):
                print(fileName[i])
            choiceFileSend = str(input('你的选择是:'))
            # 通知server要上传文件
            client.localSocket.sendto(('UPLOAD').encode(encoding='utf-8'), client.remoteAddress)
            # 通知server上传的文件名
            client.localSocket.sendto((choiceFileSend).encode(encoding='utf-8'), client.remoteAddress)
            # 利用GBN协议传输
            clientSender = GoBacktoN.GBN(Host.Host.address1, Host.Host.address2, client.localSocket, 'ClientFile/' + choiceFileSend, 'ServerFile/' + choiceFileSend)
            clientSender.serverRun()
        elif choice.upper() == 'DOWNLOAD':
            client.localSocket.sendto(('DOWNLOAD').encode(encoding='utf-8'), client.remoteAddress)
            # 获取server文件夹的文件名
            fileNames = client.localSocket.recvfrom(1024)[0].decode().split('|')
            print('请从下面文件中选择一个:')
            for i in range(len(fileNames)):
                print(fileNames[i])
            choiceFileRecv = str(input('你的选择是:'))
            # 发送想要接收的文件名
            client.localSocket.sendto((choiceFileRecv).encode(encoding='utf-8'), client.remoteAddress)
            # 利用GBN协议传输
            clientRecver = GoBacktoN.GBN(Host.Host.address1, Host.Host.address2, client.localSocket, 'ServerFile/' + choiceFileRecv, 'ClientFile/' + choiceFileRecv)
            clientRecver.clientRun()
        else:
            print('退出')
            break
