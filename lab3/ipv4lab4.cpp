/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include "sysInclude.h"
#include<stdio.h>
#include<string.h>
#include<stdlib.h>
extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

// implemented by students

/*
stud_ip_recv: receive from other, we need to check its right
pBuffer:      point to the head of IPv4
length:       the length of IPv4
*/
int stud_ip_recv(char *pBuffer,unsigned short length)
{
    int errorType=0;
    // check IPv4 header, includes Version, IP Head Length, Time to Live, Header Checksum
    // Version
    unsigned short version=((unsigned short)pBuffer[0]&0xff)>>4;
    if(version!=4)
    {
        printf("错误版本号：%d\n",version);
        errorType=STUD_IP_TEST_VERSION_ERROR;
        ip_DiscardPkt(pBuffer,errorType);
        return 1;
    }
    // IHL
    unsigned short headLength=((unsigned short)pBuffer[0]&0xff)&0xf;
    if(headLength<5)
    {
        printf("错误头部长度：%d\n",headLength);
        errorType=STUD_IP_TEST_HEADLEN_ERROR;
        ip_DiscardPkt(pBuffer,errorType);
        return 1;
    }
    // TTL
    unsigned short ttl=((unsigned short)(pBuffer+8)[0]&0xff);
    if(ttl==0)
    {
        errorType=STUD_IP_TEST_TTL_ERROR;
        ip_DiscardPkt(pBuffer,errorType);
        return 1;
    }
    // Checksum
    headLength=headLength<<2;
    unsigned int checksum=0;
    for(int i=0;i<headLength;i+=2)
    {
        unsigned int a=(unsigned int)((pBuffer+i)[0])&0xff;
        unsigned int b=(unsigned int)((pBuffer+i+1)[0])&0xff;
        checksum+=(a<<8)+b;
    }
    while(checksum>0xffff)
    {
        checksum=(checksum>>16)+(checksum&0xffff);
    }
    if((~checksum&0xffff)!=0)
    {

        errorType=STUD_IP_TEST_CHECKSUM_ERROR;
        ip_DiscardPkt(pBuffer,errorType);
        return 1;
    }
    // Destination IP
    // check could be received, Destination IP is or not Local IP or Broadcast IP
    unsigned int dstIP=ntohl(((unsigned int*)pBuffer)[4]);
    unsigned int localIP=getIpv4Address();
    if(dstIP!=0xffffffff&&dstIP!=localIP)
    {
        printf("错误dstIP，本地IP为：%d,%d\n",dstIP,localIP);
        errorType=STUD_IP_TEST_DESTINATION_ERROR;
        ip_DiscardPkt(pBuffer,errorType);
        return 1;
    }
    // send to above
    ip_SendtoUp(pBuffer+headLength,length-headLength);
    return 0;
}

/*
stud_ip_Upsend: receive from protocol above, we need to packet and send
pBuffer:        point to the head of IPv4
len:            the length of the protocol upon IPv4
srcAddr:        the address of source IPv4
dstAddr:        the address of destination IPv4
protocol:       protocol id of the one upon IPv4
ttl:            Time to Live
*/

int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
    unsigned short IPLength=((unsigned short)len&0xff)+20;
    // malloc
    char *IPBuffer=new char[IPLength];
    memset(IPBuffer,0,IPLength);
    memcpy(IPBuffer+20,pBuffer,len);
    // write IPv4 Header
    // Version and IHL
    IPBuffer[0]=0x45;
    // Type of Service
    IPBuffer[1]=0;
    // Total Length
    IPBuffer[2]=IPLength>>8;
    IPBuffer[3]=IPLength&0xff;
    // Identification
    unsigned short identification=(unsigned short)rand();
    IPBuffer[4]=identification>>8;
    IPBuffer[5]=identification&0xff;
    // DF, MF, Fragment offset
    IPBuffer[6]=0;
    IPBuffer[7]=0;
    // Time to live
    IPBuffer[8]=ttl;
    // Protocol
    IPBuffer[9]=protocol;
    //Source Address
    IPBuffer[12]=(srcAddr&0xffffffff)>>24;
    IPBuffer[13]=(srcAddr&0x00ffffff)>>16;
    IPBuffer[14]=(srcAddr&0x0000ffff)>>8;
    IPBuffer[15]=(srcAddr&0x000000ff);
    // Destination address
    IPBuffer[16]=(dstAddr&0xffffffff)>>24;
    IPBuffer[17]=(dstAddr&0x00ffffff)>>16;
    IPBuffer[18]=(dstAddr&0x0000ffff)>>8;
    IPBuffer[19]=(dstAddr&0x000000ff);
    //Header checksum
    unsigned int checksum=0;
    for(int i=0;i<20;i+=2)
    {
        unsigned int a=(unsigned int)(IPBuffer+i)[0]&0xff;
        unsigned int b=(unsigned int)(IPBuffer+i+1)[0]&0xff;
        checksum+=(a<<8)+b;
    }
    while(checksum>0xffff)
    {
        checksum=(checksum>>16)+(checksum&0xffff);
    }
    checksum=((~checksum)&0xffff);
    IPBuffer[10]=checksum>>8;
    IPBuffer[11]=checksum&0xff;
    // send
    ip_SendtoLower(IPBuffer,IPLength);
	return 0;
}
