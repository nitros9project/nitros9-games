/* CoCo 3 Level 2 tick rate. */
sleep(seconds)
int seconds;
{
    while (seconds-- > 0) tsleep(60);
}
