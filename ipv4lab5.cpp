/*
* THIS FILE IS FOR IP FORWARD TEST
*/
#include "sysInclude.h"
#include<map>
using namespace std;
// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students

/*
stud_Route_Init: initial the routing table
routingTable:    <Destination,stud_route_msg>
*/
map<unsigned int,stud_route_msg*> routingTable;
void stud_Route_Init()
{
	return;
}


/*
stud_route_add add message to the routing table
*/
void stud_route_add(stud_route_msg *proute)
{
    unsigned int dstIP=ntohl(proute->dest);
    stud_route_msg* route=(stud_route_msg*)malloc(sizeof(stud_route_msg));
    memcpy(route,proute,sizeof(stud_route_msg));
    routingTable[dstIP]=route;
	return;
}

/*
stud_fwd_deal: receive from protocol below, deal it according to the routing message
*/
int stud_fwd_deal(char *pBuffer, int length)
{
    // the local set to be received
    unsigned int dstAddr=ntohl(((unsigned int*)pBuffer)[4]);
    unsigned int localAddr=getIpv4Address();
    if(localAddr==dstAddr)
    {
        fwd_LocalRcv(pBuffer,length);
        return 0;
    }
    // find in routing table to make sure the next step
    stud_route_msg* route=routingTable[srcAddr];
    // the wrong set to be discarded
    if(route==NULL)
    {
        fwd_DiscardPkt(pBuffer,STUD_FORWARD_TEST_NOROUTE);
        return 1;
    }
    // check TTL
    unsigned short ttl=((unsigned short)(pBuffer+8)[0]&0xff);
    if(ttl==0)
    {
        fwd_DiscardPkt(pBuffer,STUD_FORWARD_TEST_TTLERROR);
        return 1;
    }
    // the transmit set to be transmitted
    unsigned int nextIP=route->nexthop;
    // reset checksum
    ((unsigned short*)pBuffer)[5]=0;
    // TTL-1
    pBuffer[8]-=1;
    // recount checksum
    unsigned short headLength=((unsigned short)pBuffer[0]&0xff)&0xf;
    headLength=headLength<<2;
    unsigned int checksum=0;
    for(int i=0;i<headLength;i+=2)
    {
        unsigned int a=(unsigned int)(pBuffer+i)[0]&0xff;
        unsigned int b=(unsigned int)(pBuffer+i+1)[0]&0xff;
        checksum+=(a<<8)+b;
    }
    while(checksum>0xffff)
    {
        checksum=(checksum>>16)+(checksum&0xffff);
    }
    checksum=((~checksum)&0xffff);
    pBuffer[10]=checksum>>8;
    pBuffer[11]=checksum&0xff;
    // fwd_SenttoLower
    fwd_SendtoLower(pBuffer,length,nextIP);
	return 0;
}
