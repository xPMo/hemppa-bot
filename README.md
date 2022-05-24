# A Bot based on Hemppa

Current status can be found [here](https://github.com/xPMo/hemppa-bot/issues/1).

## How to use this:

1. Once: `./prep.sh`.
2. Replace the encrypted `.env` with yours, including the environment variables Hemppa needs to run.
My current `.env` contains the following information:

```sh
MATRIX_ACCESS_TOKEN='<REDACTED>'

SERV='jupiterbroadcasting.com'
MATRIX_USER="@gammabot:$SERV"
MATRIX_SERVER="https://colony.$SERV"

BOT_OWNERS="@gammafunction:matrix.org,@gamma:$SERV,@bmeares:$SERV"
TZ="US/Central"
```

3. Run `./start.sh`.
