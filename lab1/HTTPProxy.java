package lab1;

import java.io.IOException;
import java.net.ServerSocket;

public class HTTPProxy {
	static int timeOut = 1000;// 超时时间
	static boolean userFilter = false;// 用户过滤
	static boolean pageFilter = true;// 网页过滤
	static boolean pageRetrace = true;// 网站引导
	static ServerSocket serverSocket;// 监听客户端请求的套接字
	static int listenPort = 10240;// 监听端口号

	public static void RunProxy() {
		try {
			serverSocket = new ServerSocket(listenPort);// 新建一个与客户端通信的套接字
			System.out.println("监听端口:" + listenPort);
			if (userFilter == true) {
				System.out.println("用户过滤开启");
			}
			if (pageFilter == true) {
				System.out.println("网页过滤开启");
			}
			if (pageRetrace == true) {
				System.out.println("网站引导开启");
			}
			System.out.println("服务器缓存开启");
			while (true) {
				new MyThread(serverSocket.accept()).start();// 新建子线程处理连接请求
			}
		} catch (IOException e) {
			System.out.println(e.getMessage());
		}
	}

	public static void main(String[] args) {
		HTTPProxy.RunProxy();
	}
}
