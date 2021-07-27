class Host:
    address1 = ('127.0.0.1', 12340)
    address2 = ('127.0.0.1', 12341)

    @staticmethod
    def makePacket(pktNum, data):
        return (str(pktNum) + ' ' + str(data)).encode(encoding='utf-8')
