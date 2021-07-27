package lab1;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

public class MyThread extends Thread {
	Socket proxyClientSocket;// 与客户端通信的代理服务器的套接字
	Socket proxyServerSocket;// 与服务器端通信的代理服务器的套接字
	String clientToProxyString = "";// 接收来自客户端的请求报文
	String serverToProxyString = "";// 接受来自服务器的响应报文
	byte[] serverToProxyByte;// 用于储存接受的响应报文字节流信息
	int port = 80;// 默认与服务器的连接端口为80
	String url;// 头部行中的url
	String host;// 头部行中的host
	String wantPageFilter = "cs.hit.edu.cn";
	String wantUserFilter = "127.0.0.1";
	String wantPageRetraceFrom = "jwes.hit.edu.cn";
	String wantPageRetraceTo = "www.7k7k.com";

	public MyThread(Socket proxyClientSocket) {
		this.proxyClientSocket = proxyClientSocket;
	}

	public boolean FilterRetrace() throws IOException {
		if (!HTTPProxy.userFilter && !HTTPProxy.pageFilter) {
			return false;
		}
		// 若开启了用户过滤且客户端用户为被限制用户，则返回false
		if (HTTPProxy.userFilter && wantUserFilter.contains(this.proxyClientSocket.getInetAddress().getHostAddress())) {
			System.out.println("用户受限:" + this.proxyClientSocket.getInetAddress().getHostAddress());
			return true;
		}
		// 若开启了网站过滤且目的主机为被过滤的主机，则返回
		else if (HTTPProxy.pageFilter && wantPageFilter.equals(this.host)) {
			System.out.println("网站受限:" + this.host);
			return true;
		}
		// 若开启了网站引导且目的主机为被引导的主机则将头部行替换
		else if (HTTPProxy.pageRetrace && wantPageRetraceFrom.equals(this.host)) {
			String old_host = this.host;
			this.host = wantPageRetraceTo;
			this.port = 80;
			this.url = this.url.replace(old_host, this.host);
			this.clientToProxyString = this.clientToProxyString.replace(old_host, this.host);// 将请求报文中的头部url替换为引导网站的url
			System.out.println("网站引导:" + this.host);
			return false;
		}
		return false;
	}

	public void cache() throws IOException {
		if (!new File("src/file/" + this.host).exists()) {
			new File("src/file/" + this.host).mkdir();
		}
		File cacheFile = new File("src/file/" + this.host + "/" + this.url.hashCode() + ".txt");
		PrintWriter proxyToServer = new PrintWriter(proxyServerSocket.getOutputStream());// 向服务器发送的流
		InputStream serverToProxy = proxyServerSocket.getInputStream();// 服务器向客户端返回响应的流
		OutputStream proxyToClient = proxyClientSocket.getOutputStream();// 向客户端发送的流
		if (!cacheFile.exists()) {
			System.out.println("缓存文件不存在，需转发请求，文件名:" + this.url.hashCode());
			FileOutputStream cacheFileOut = new FileOutputStream(cacheFile);// 写缓存文件的流
			System.out.println("没有用cache的文件头部："+this.clientToProxyString);
			proxyToServer.write(clientToProxyString); // 向服务器转发原请求
			proxyToServer.flush();
			while (true) {
				try {
					proxyServerSocket.setSoTimeout(HTTPProxy.timeOut);// 设置超时时间用于跳出阻塞状态
					int b = serverToProxy.read();// 字节流读取响应报文
					if (b == -1) {
						break;
					} else {
						cacheFileOut.write(b);// 写入到缓存文件中
						proxyToClient.write(b);// 写入到向客户端发送响应的流
						proxyServerSocket.setSoTimeout(0);
					}
				} catch (SocketTimeoutException e) {
					break;
				}
			}
			System.out.println("响应报文来源:服务器端\t新建缓存:是\t文件名:" + this.url.hashCode() + ".txt");
			cacheFileOut.close();
		}
		// cache文件已经存在
		else {
			DateFormat df = new SimpleDateFormat("EEE, d MMM yyyy HH:mm:ss z", Locale.ENGLISH);
			df.setTimeZone(TimeZone.getTimeZone("GMT"));
			this.clientToProxyString = this.clientToProxyString.replace("\r\n\r\n",
					"\r\nIf-Modified-Since: " + df.format(cacheFile.lastModified()) + "\r\n\r\n");
			System.out.println("用到cache文件头部："+this.clientToProxyString);
			proxyToServer.write(clientToProxyString);
			proxyToServer.flush();
			// 接收服务器的请求
			List<Byte> bytes = new ArrayList<>();
			while (true) {
				try {
					proxyServerSocket.setSoTimeout(HTTPProxy.timeOut);// 设置超时时间用于跳出流阻塞
					int b = serverToProxy.read();// 读取响应报文
					if (b == -1) {
						break;
					} else {
						bytes.add((byte) (b));
						proxyServerSocket.setSoTimeout(0);
					}
				} catch (SocketTimeoutException e) {
					break;
				}
			}
			this.serverToProxyByte = new byte[bytes.size()];
			int count = 0;// 用于构造响应字节报文
			for (Byte temp : bytes) {
				this.serverToProxyByte[count++] = temp;
			}
			this.serverToProxyString = new String(serverToProxyByte, 0, count);// 构造文本响应报文
			System.out.println(this.serverToProxyString);
			if (this.serverToProxyString.split("\r\n")[0].contains("304")) {// 响应报文头含304，则缓存可用
				System.out.println("缓存命中: " + this.url + "\t文件名: " + this.url.hashCode());
				FileInputStream cacheFileWrite = new FileInputStream(cacheFile);
				int b;// 直接将缓存报文发送给客户端
				while ((b = cacheFileWrite.read()) != -1) {
					proxyToClient.write(b);// 写入客户端的流
				}
				cacheFileWrite.close();
				System.out.println("响应报文来源:缓存文件\t更新缓存:否\t文件名:" + this.url.hashCode() + ".txt");
			} else if (this.serverToProxyString.split("\r\n")[0].contains("200")) {// 响应报文头含200，更新缓存
				System.out.println("缓存文件存在，但需更新，文件名:" + this.url.hashCode());
				FileOutputStream cacheFileOut = new FileOutputStream(cacheFile);// 写缓存文件的流
				proxyToClient.write(this.serverToProxyByte);// 将从服务器读取到的转发给客户端
				cacheFileOut.write(this.serverToProxyByte);// 更新本地缓存
				cacheFileOut.close();
				System.out.println("响应报文来源:服务器端\t更新缓存:是\t文件名:" + this.url.hashCode() + ".txt");
			}
		}
	}

	@Override
	public void run() {
		try {
			BufferedReader reader = new BufferedReader(new InputStreamReader(proxyClientSocket.getInputStream()));// 用于读取客户端发出的请求报文
			String line = reader.readLine();
			if (line == null) {
				return;
			}
			System.out.println("请求头部行：" + line);
			this.parse(line);// 解析头部行，并设置对象的属性值
			while (line != null) {
				try {
					clientToProxyString += line + "\r\n";// 获取请求报文的信息
					proxyClientSocket.setSoTimeout(HTTPProxy.timeOut);// 设置超时时间，用于跳出流的阻塞状态
					line = reader.readLine();
					proxyClientSocket.setSoTimeout(0);
				} catch (SocketTimeoutException e) {
					break;
				}
			}
			if (this.FilterRetrace()) {// 网站过滤，用户过滤，钓鱼
				return;
			}
			proxyServerSocket = new Socket(this.host, this.port);// 建立与服务器通信的套接字
			this.cache();
			proxyServerSocket.close();
			proxyClientSocket.close();
		} catch (IOException e) {
			System.out.println("\n" + e.getMessage());
		}
	}

	public void parse(String headLine) {
		this.url = headLine.split(" ")[1];// 获取请求的目的url
		int index = -1;
		this.host = this.url;// 下面用于获取请求的主机名
		// 去掉http://
		if ((index = this.host.indexOf("http://")) != -1) {
			this.host = this.host.substring(index + 7);
		}
		// 去掉https://
		if ((index = this.host.indexOf("https://")) != -1) {
			this.host = this.host.substring(index + 8);
		}
		// 去掉/
		if ((index = this.host.indexOf("/")) != -1) {
			this.host = this.host.substring(0, index);
		}
		// 去掉:
		if ((index = this.host.indexOf(":")) != -1) {
			this.port = Integer.valueOf(this.host.substring(index + 1));
			this.host = this.host.substring(0, index);
		}
	}
}
