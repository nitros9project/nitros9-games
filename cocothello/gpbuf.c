/* Get/put buffer commands, using c3's register-first argument ABI. */
static putword(p, n)
char *p;
int n;
{
    p[0] = n >> 8;
    p[1] = n;
}

KilBuf(path, group, buffer)
int path, group, buffer;
{
    char cmd[4];
    cmd[0] = 27; cmd[1] = 0x2a;
    cmd[2] = group; cmd[3] = buffer;
    return write(path, cmd, 4);
}

GPLoad(path, group, buffer, type, width, height, size)
int path, group, buffer, type, width, height, size;
{
    char cmd[11];
    cmd[0] = 27; cmd[1] = 0x2b;
    cmd[2] = group; cmd[3] = buffer; cmd[4] = type;
    putword(cmd+5, width); putword(cmd+7, height); putword(cmd+9, size);
    return write(path, cmd, 11);
}

PutBlk(path, group, buffer, x, y)
int path, group, buffer, x, y;
{
    char cmd[8];
    cmd[0] = 27; cmd[1] = 0x2d;
    cmd[2] = group; cmd[3] = buffer;
    putword(cmd+4, x); putword(cmd+6, y);
    return write(path, cmd, 8);
}

DfnGPBuf(path,group,buffer,size)
int path,group,buffer,size;
{
    char c[6];
    c[0]=27; c[1]=0x29; c[2]=group; c[3]=buffer;
    putword(c+4,size);
    return write(path,c,6);
}
GetBlk(path,group,buffer,x,y,width,height)
int path,group,buffer,x,y,width,height;
{
    char c[12];
    c[0]=27; c[1]=0x2c; c[2]=group; c[3]=buffer;
    putword(c+4,x); putword(c+6,y); putword(c+8,width); putword(c+10,height);
    return write(path,c,12);
}
