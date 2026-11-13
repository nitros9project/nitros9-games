/*
    solitaire.h
*/
 char *letters[] = {"A ","2 ","3 ","4 ","5 ","6 ","7 ","8 ",
                    "9 ","10","J ","Q ","K "};
 char spade[] = {'0','0','0','0','1','0','0','0','0','0',
                 '0','0','0','1','1','1','0','0','0','0',
                 '0','0','1','1','1','1','1','0','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','0','1','1','1','1','1','0','0','0',
                 '0','0','0','0','1','0','0','0','0','0',
                 '0','0','0','1','1','1','0','0','0','0',
                 '0','0','1','1','1','1','1','0','0','0',
                 '0','1','1','1','1','1','1','1','0','0'};
 char heart[] = {'0','0','1','1','0','1','1','0','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','1','1','1','1','1','1','1','0','0',
                 '0','0','1','1','1','1','1','0','0','0',
                 '0','0','1','1','1','1','1','0','0','0',
                 '0','0','0','1','1','1','0','0','0','0',
                 '0','0','0','1','1','1','0','0','0','0',
                 '0','0','0','0','1','0','0','0','0','0',
                 '0','0','0','0','1','0','0','0','0','0'};
 char club[] = {'0','0','0','0','1','1','0','0','0','0',
                '0','0','0','1','1','1','1','0','0','0',
                '0','0','0','1','1','1','1','0','0','0',
                '0','1','1','0','1','1','0','1','1','0',
                '1','1','1','1','1','1','1','1','1','1',
                '1','1','1','1','1','1','1','1','1','1',
                '0','1','1','0','1','1','0','1','1','0',
                '0','0','0','0','1','1','0','0','0','0',
                '0','0','0','1','1','1','1','0','0','0',
                '0','0','1','1','1','1','1','1','0','0',
                '0','1','1','1','1','1','1','1','1','0'};
 char diamond[] = {'0','0','0','0','0','0','0','0','0','0',
                   '0','0','0','0','1','1','0','0','0','0',
                   '0','0','0','1','1','1','1','0','0','0',
                   '0','0','1','1','1','1','1','1','0','0',
                   '0','1','1','1','1','1','1','1','1','0',
                   '1','1','1','1','1','1','1','1','1','1',
                   '0','1','1','1','1','1','1','1','1','0',
                   '0','0','1','1','1','1','1','1','0','0',
                   '0','0','0','1','1','1','1','0','0','0',
                   '0','0','0','0','1','1','0','0','0','0',
                   '0','0','0','0','0','0','0','0','0','0'};

d_suit (p,x,y)
 char *p;
 int x,y;
{
    int i, j, k, l;

    i = x;
    j = y;
    for(k=1;k<12;++k) {
        for(l=1;l<21;++l) {
            SetDPtr(path,i,j);
            if(*p=='1') {
                RPoint(path,0,0);
            }
        if((l-l/2*2)==0)
            ++p;
        ++i;
        }
    i=x;
    ++j;
    }
}
d_card(i,j,card,suit)
 int i, j, card, suit;
{
    int color;
    int cx, cy;
    char card_name[3];

    PSet(path,0,0);
    FColor(path,BLACK);
    SetDPtr(path,i,j);
    Box(path,i+60,j+44);
    if (card == -3) {
        FColor(path,RED);
        SetDPtr(path,i,j);
        Box(path,i+60,j+44);
        return;
    }
    if (card == -2) {
        FColor(path,RED);
        PSet(path,GRP_PAT4,PAT_XHTC);
        SetDPtr(path,i+1,j+1);
        Bar(path,i+57,j+43);
    }
    else {
        if (card == -1)
            FColor(path,BLACK);
        else
            FColor(path,WHITE);
        SetDPtr(path,i+2,j+1);
        Bar(path,i+58,j+43);
    }
    if (card < 0) {
        PSet(path,0,0);
        return;
    }
    if((suit==0)||(suit==2))
        color = BLACK;
    else
        color = RED;
    FColor(path,color);
    BColor(path,WHITE);
    cx = i/12;
    cy = j/8;
    PutBlk(path,grpnum,card+13*suit+1,i+2,j+2);
    cx+=3;
    cy+=2;
    PutBlk(path,grpnum,card+13*suit+1,i+31,j+24);

}
dfn_stuff()
{
    int     i, j, k, l;
    char    *suits[4];

    suits[0] = spade;
    suits[1] = heart;
    suits[2] = club;
    suits[3] = diamond;

 /* Generate get/put buffers */
    LSet(path,0);
    for(i=0; i<4; ++i) {
        FColor(path,WHITE);
        SetDPtr(path,0,0);
        Bar(path,30,11);
        if((i==0)||(i==2))
            j = BLACK;
        else
            j = RED;
        FColor(path,j);
        d_suit(suits[i],2,0);
        DfnGPBuf(path,grpnum,i+100,274);
        GetBlk(path,grpnum,i+100,0,0,22,11);
    }
    BColor(path,WHITE);
    l = 0;
    k = BLACK;
    for(j=0, i=0; i<52; ++i) {
        FColor(path,WHITE);
        SetDPtr(path,0,0);
        Bar(path,60,30);
        FColor(path,k);
        if(strcmp(letters[j],"10")==0)
            Font(path,GRP_FONT,FNT_S6X8);
        else
            Font(path,GRP_FONT,FNT_S8X8);
        CurXY(path,1,0);
        puts(letters[j]);
        PutBlk(path,grpnum,l+100,12,8);
        DfnGPBuf(path,grpnum,i+1,500);
        GetBlk(path,grpnum,i+1,10,0,27,20);
        ++j;
        if(j==13) {
            j = 0;
            ++l;
            if(k==BLACK)
                k = RED;
            else
                k = BLACK;
            }
        FColor(path,k);
    }
    FColor(path,BLUE);
    SetDPtr(path,0,0);
    Bar(path,60,30);
}
sighandler(sig)
int sig;
{
    sigcode=sig;
    _ss_msig(path,MOUSSIG);
}
check_loc(x, y, v, i, j)
 int x, y, *v, *i, *j;
{
    int     t, u;
    *v = 0;
    *i = -1;
    *j = -1;
    if((x>7)&&(x<69)) {
        if((y>93)&&(y<139))
            *v = 1;
        else
            if((y>19)&&(y<65))
                *v = 2;
        return;
    }
    for(t=0; t<7; ++t)
        for(u=0; u<t+1; ++u) {
            if((x>=xpos[t][u])&&(x<xpos[t][u]+61))
                if((y>=ypos[t][u])&&(y<ypos[t][u]+45))
                    if(pyr[t][u].card>=0) {
                        *v = 3;
                        *i = t;
                        *j = u;
                    }
        }
    if(*v==3)
        return;
    if((x>518)&&(x<567))
        if((y>55)&&(y<64))
            *v = 4;
    if((x>518)&&(x<602))
        if((y>71)&&(y<80))
            *v = 5;
    if((x>518)&&(x<593))
        if((y>87)&&(y<96))
            *v = 6;
}
new_display()
{
    int     i, j, k, l, m, t[52];
    struct sgtbuf tim;
    _ss_mous(path,UPDATE,TIMEOUT,0);
    Font(path,GRP_FONT,FNT_S6X8);
    some_used = FALSE;
    won_game = 0;
/*  ramdomize */
    getime(&tim);
    i = tim.t_hour;
    j = tim.t_minute;
    k = tim.t_second;
    l = 3600 * i + 60 * j + k;
    srand(l);
/*  shuffle the cards */
    for (i=0; i<52; ++i)
        t[i] = 0;
    for (dptr=0; dptr<52; ) {
        i = rand()/630;
        if (i>51)
            i = 51;
        if (t[i]==0) {
            t[i] = 1;
            if (i<13) {
                deck[dptr].card = i;
                deck[dptr].suit = 0;
            }
            else
                if (i<26) {
                    i-=13;
                    deck[dptr].card = i;
                    deck[dptr].suit = 1;
                }
                else
                    if (i<39) {
                        i-=26;
                        deck[dptr].card = i;
                        deck[dptr].suit = 2;
                    }
                    else {
                        i-=39;
                        deck[dptr].card = i;
                        deck[dptr].suit = 3;
                    }
            ++dptr;
        }
    }
    SetGC(path,0,0);

    FColor(path,RED);
    BColor(path,BLUE);
    Clear(path);
    Font(path,GRP_FONT,FNT_S6X8);
    CurXY(path,34,1);
    puts("Pyramid Solitaire");
    CurXY(path,41,2);
    puts("by");
    CurXY(path,36,3);
    puts("ColorSystems");
    CurXY(path,39,4);
    puts("c 1989");
    SetDPtr(path,475,36);
    Circle(path,9);
    CurXY(path,43,7);
    puts("QUIT");
    CurXY(path,43,9);
    puts("RE-DEAL");
    CurXY(path,43,11);
    puts("CANCEL");

    m = 290;
    l = 4;
    dptr = 0;
    for (i=0; i<7; ++i) {
        k = m;
        for (j=0; j<i+1; ++j) {
            xpos[i][j] = k;
            ypos[i][j] = l;
            pyr[i][j].card = deck[dptr].card;
            pyr[i][j].suit = deck[dptr].suit;
/*            if((i==0)&&(j==0))
                ;
            else {
                DfnGPBuf(path,grpnum,(i*7)+j+100,3000);
                GetBlk(path,grpnum,(i*7)+j+1,xpos[i][j],ypos[i][j],xpos[i][j]+60,ypos[i][j]+44);
            }*/
            d_card(xpos[i][j],ypos[i][j],pyr[i][j].card,pyr[i][j].suit);
            ++dptr;
            k+=68;
        }
        l+=22;
        m-=34;

    }

    FColor(path,RED);
    BColor(path,BLUE);
    CurXY(path,1,1);
    puts("Deck");
    d_card(8,20,-2,0);
    FColor(path,RED);
    BColor(path,BLUE);
    CurXY(path,1,10);
    puts("Pile");
    d_card(8,94,-1,0);

    pptr = 0;
    selcnt = 0;
}
deal_deck()
{
    int     i, j;
    if(dptr==52) {
        if(ONCE) {
            FColor(path,RED);
            BColor(path,BLUE);
            CurXY(path,19,23);
            write(path,"Deck is empty!",14);
            Bell(path);
            tsleep(120);
            CurXY(path,19,23);
            ErEOLine(path);
            return;
        }
        else {
            if (some_used) {
                some_used = FALSE;
                for(j = 0, i = 52-pptr; i<52; ++i, ++j) {
                    deck[i].card = pile[j].card;
                    deck[i].suit = pile[j].suit;
                }
                dptr = 52 - pptr;
                pptr = 0;
                d_card(8,94,-1,0);
                d_card(8,20,-2,0);
            }
            else {
                FColor(path,RED);
                BColor(path,BLUE);
                CurXY(path,21,23);
                Bell(path);
                write(path,"Game over!",10);
                Bell(path);
                tsleep(30);
                CurXY(path,21,23);
                ErEOLine(path);
                return;
            }
        }
    }
    de_sel();
    for(i=0; i<3; ++i) {
        pile[pptr].card = deck[dptr].card;
        pile[pptr].suit = deck[dptr].suit;
        ++pptr;
        ++dptr;
    d_card(8,94,-1,0);
    d_card(8,94,pile[pptr-1].card,pile[pptr-1].suit);
        if(dptr==52)
            i = 3;
    }
    if(dptr==52)
        d_card(8,20,-1,0);
}
