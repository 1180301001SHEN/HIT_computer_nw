import random
import select
import Host


class SR(object):
    def __init__(self, localAddress, remoteAddress, localSocket, filePath, savePath):
        # 窗口大小
        self.windowSize = 4
        # 窗口起始位置
        self.sendBase = 0
        # 窗口结束位置
        self.nextSeq = 0
        # 计时器
        self.timeCounts = {}
        # 接受ack的缓存
        self.ackSeq = {}
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
        # 服务器端接受的ack报文大小
        self.ackSize = 10
        # 接收端的窗口大小
        self.rcvWindowSize = 4
        # 客户端rcvfrom的数据大小
        self.dataSize = 1678
        # 期待下一次接受的序列号
        self.expSeq = 0
        # 客户端窗口起始位置
        self.rcvBase = 0
        # 客户端接受到的数据缓存
        self.rcvData = {}
        # 将数据写入文件
        self.savePath = savePath
        # 丢包率(数据丢包,ack丢包)
        self.pktLossRate = 0.1
        self.ackLossRate = 0

    # server向client发送数据
    def sendData(self):
        # 如果已经发到结尾就直接返回
        if self.nextSeq == len(self.data):
            print("发送完毕")
            return
        # 窗口中还有没发送的数据,就发送
        if self.nextSeq - self.sendBase < self.windowSize:
            if random.random() > self.pktLossRate:
                self.socket.sendto(Host.Host.makePacket(self.nextSeq, self.data[self.nextSeq]), self.remoteAddress)
            # 设置计时器和等待ack的缓存
            self.timeCounts[self.nextSeq] = 0
            self.ackSeq[self.nextSeq] = False
            print('服务器成功发送数据:', str(self.nextSeq))
            self.nextSeq += 1
        # 窗口满了就先不发送,等待client发送ack
        else:
            print('服务器窗口已满')

    # 超时处理
    def handleTimeOut(self, timeOutSeq):
        print('超时重传')
        self.timeCounts[timeOutSeq] = 0
        # 重传需要重传的数据
        if random.random() > self.pktLossRate:
            self.socket.sendto(Host.Host.makePacket(timeOutSeq, self.data[timeOutSeq]), self.remoteAddress)
        print('服务器重传数据:', str(timeOutSeq))

    # 从文件中读取数据,并存在data数组中
    def getData(self):
        f = open(self.filePath, 'r', encoding='utf-8')
        while True:
            tempData = f.read(512)
            if len(tempData) <= 0:
                break
            self.data.append(tempData)

    # 滑动发送窗口
    def SlideSendWindow(self):
        # 将从sendBase以后已经接受到ack的全都删除
        while self.ackSeq.get(self.sendBase):
            del self.ackSeq[self.sendBase]
            del self.timeCounts[self.sendBase]
            self.sendBase += 1

    # 服务器端运行
    def serverRun(self):
        while True:
            self.sendData()
            # 监控并接受三个通信列表
            read = select.select([self.socket], [], [], 1)[0]
            # 有数据返回,就解析出来rcvACK
            if len(read) > 0:
                rcvACK = self.socket.recvfrom(self.ackSize)[0].decode().split()[0]
                if self.sendBase <= int(rcvACK) < self.nextSeq:
                    print('有用ACK:', rcvACK)
                    self.ackSeq[int(rcvACK)] = True
                    if self.sendBase == int(rcvACK):
                        self.SlideSendWindow()
                else:
                    print('无用ACK', rcvACK)
            # 对缓存中的么一个未接收到ack的time+1
            for i in self.timeCounts.keys():
                if not self.ackSeq[i]:
                    self.timeCounts[i] += 1
                    if self.timeCounts[i] > self.timeOut:
                        self.handleTimeOut(i)
            # server发送完毕就停止
            if self.sendBase == len(self.data):
                self.socket.sendto(Host.Host.makePacket(0, 0), self.remoteAddress)
                print('服务器发送完毕')
                break

    # 将接受到的数据写回文件中
    def writeFile(self, data):
        with open(self.savePath, 'a', encoding='utf-8') as f:
            f.write(data)

    # 滑动接受窗口
    def SlideRcvWindow(self):
        # 将从rcvBase以后已经接受到ack的全都删除
        while self.rcvData.get(self.rcvBase) is not None:
            self.writeFile(self.rcvData.get(self.rcvBase))
            del self.rcvData[self.rcvBase]
            self.rcvBase += 1

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
                print('客户端收到数据:', rcvSeq)
                # 在正常范围内的rcvSeq都接受并返回ack
                if self.rcvBase - self.rcvWindowSize <= int(rcvSeq) < self.rcvBase + self.rcvWindowSize:
                    if self.rcvBase <= int(rcvSeq) < self.rcvBase + self.rcvWindowSize:
                        self.rcvData[int(rcvSeq)] = rcvData
                        if int(rcvSeq) == self.rcvBase:
                            self.SlideRcvWindow()
                    if random.random() >= self.ackLossRate:
                        self.socket.sendto(Host.Host.makePacket(int(rcvSeq), 0), self.remoteAddress)
                    print('客户端发送ACK:', rcvSeq)
