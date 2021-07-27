import Host
import SelectiveRepeat
import GoBacktoN
import threading
import socket


def RunGBN():
    socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket1.bind(Host.Host.address1)
    host1 = GoBacktoN.GBN(Host.Host.address1, Host.Host.address2, socket1, 'file/3.txt', 'file/2.txt')

    socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket2.bind(Host.Host.address2)
    host2 = GoBacktoN.GBN(Host.Host.address2, Host.Host.address1, socket2, 'file/3.txt', 'file/2.txt')
    threading.Thread(target=host1.serverRun).start()
    threading.Thread(target=host2.clientRun).start()


def RunSR():
    socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket1.bind(Host.Host.address1)
    host1 = SelectiveRepeat.SR(Host.Host.address1, Host.Host.address2, socket1, 'file/3.txt', 'file/2.txt')

    socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket2.bind(Host.Host.address2)
    host2 = SelectiveRepeat.SR(Host.Host.address2, Host.Host.address1, socket2, 'file/3.txt', 'file/2.txt')
    threading.Thread(target=host1.serverRun).start()
    threading.Thread(target=host2.clientRun).start()


if __name__ == "__main__":
    a = input('GBN or SR?')
    if a == 'GBN':
        RunGBN()
    elif a == 'SR':
        RunSR()
