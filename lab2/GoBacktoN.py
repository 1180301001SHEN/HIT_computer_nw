import random
import select
import Host


class GBN(object):
    def __init__(self, localAddress, remoteAddress, localSocket, filePath, savePath):
        # 窗口大小
        self.windowSize = 4
        # 窗口的起始位置
        self.sendBase = 0
        # 窗口的结束位置
        self.nextSeq = 0
        # 计时器
        self.timeCount = 0
        # 超时设置
        self.timeOut = 5
        # 本机地址和目标地址
        self.localAddress = localAddress
        self.remoteAddress = remoteAddress
        # 绑定套接字
        self.socket = localSocket
        # 需要传输的数据
        self.data = []
        self.filePath = filePath
        self.getData()
        # 服务器端接受ack报文的大小
        self.ackSize = 10
        # 客户端rcvfrom的数据大小
        self.dataSize = 1678
        # 期望下一次接受的序列号
        self.expSeq = 0
        # 将数据写入文件
        self.savePath = savePath
        # 丢包率(数据丢包,ack丢包)
        self.pktLossRate = 0.1
        self.ackLossRate = 0

    # server向client发送数据
    def sendData(self):
        # 如果已经发到结尾就直接返回
        if self.nextSeq == len(self.data):
            print("发送完毕,共:", self.nextSeq)
            return
        # 窗口中还有没发送的数据,就发送
        if self.nextSeq - self.sendBase < self.windowSize:
            if random.random() > self.pktLossRate:
                self.socket.sendto(Host.Host.makePacket(self.nextSeq, self.data[self.nextSeq]), self.remoteAddress)
            print('服务器成功发送数据:', str(self.nextSeq))
            self.nextSeq += 1
        # 窗口满了就先不发送,等待client发送ack
        else:
            print('服务器窗口已满')

    # 超时处理
    def handleTimeOut(self):
        print('超时重传')
        self.timeCount = 0
        # 把窗口内的所有数据全都重新传一遍
        for i in range(self.sendBase, self.nextSeq):
            if random.random() > self.pktLossRate:
                self.socket.sendto(Host.Host.makePacket(i, self.data[i]), self.remoteAddress)
                print('服务器重传数据:', str(i))

    # 从文件中读取数据,并存在data数组中
    def getData(self):
        f = open(self.filePath, 'r', encoding='utf-8')
        while True:
            tempData = f.read(512)
            if len(tempData) <= 0:
                break
            self.data.append(tempData)

    # 服务器端运行
    def serverRun(self):
        while True:
            self.sendData()
            # 监控并接受三个通信列表
            read = select.select([self.socket], [], [], 1)[0]
            # 有数据返回,就解析出来rcvACK
            if len(read) > 0:
                rcvACK = self.socket.recvfrom(self.ackSize)[0].decode().split()[0]
                print('收到ACK', rcvACK)
                self.sendBase = int(rcvACK) + 1
                self.timeCount = 0
            # 没有就time+1
            else:
                self.timeCount += 1
                if self.timeCount > self.timeOut:
                    self.handleTimeOut()
            # server发送完毕就停止
            if self.sendBase == len(self.data):
                self.socket.sendto(Host.Host.makePacket(0, 0), self.remoteAddress)
                print('服务器发送完毕')
                break

    # 将接受到的数据写回文件中
    def writeFile(self, data):
        with open(self.savePath, 'a', encoding='utf-8') as f:
            f.write(data)

    # 客户端运行
    def clientRun(self):
        while True:
            # 监控并接受三个通信列表
            read = select.select([self.socket], [], [], 1)[0]
            # 有数据传过来,就解析出序列号和数据
            if len(read) > 0:
                rcvData = self.socket.recvfrom(self.dataSize)[0].decode()
                rcvSeq = rcvData.split()[0]
                rcvData = rcvData.replace(rcvSeq + ' ', '')
                # 以'0 0'为结束标志
                if rcvSeq == '0' and rcvData == '0':
                    print('传输结束')
                    break
                # 接受到期望收到的数据
                if int(rcvSeq) == self.expSeq:
                    print('收到期望的序列数据')
                    self.writeFile(rcvData)
                    self.expSeq += 1
                # 否则就直接丢弃
                else:
                    print('收到非期望的序列数据')
                # 以一定概率重传
                if random.random() >= self.ackLossRate:
                    self.socket.sendto(Host.Host.makePacket(self.expSeq - 1, 0), self.remoteAddress)
