import websockets
import asyncio
import json
import logging
import logging.config

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('tradebot')


PERCENT = 0.008
BIDDING_PERCENT = 0.003

add_one_percent = lambda x: round(x * (1 + PERCENT/2), 4)
sub_one_percent = lambda x: round(x * (1 - PERCENT/2), 4)
add_half_percent = lambda x : round(x * (1 + PERCENT / 2), 4)

add_bidding_percent = lambda x: round(x * (1 + BIDDING_PERCENT), 4)

url = 'wss://api.bitfinex.com/ws'

async def get_ticker():
    while True:
        try:
            async with websockets.connect(url) as websocket:
                logger.debug('connected')
                request = {
                   "event":"subscribe",
                   "channel":"ticker",
                   "pair":"IOTUSD"
                }
                await websocket.send(json.dumps(request))

                while True:
                    ticker = json.loads(await websocket.recv())
                    if len(ticker) == 11:
                        yield ticker[1]
        except Exception:
            logger.debug('Connection lost. Retrying')

#test_data = [
#     #1.7424, 1.7428,
#     1.74, 1.7399, # falling
#     1.7493, 1.7488, 1.735, #raising
#     1.7451, 1.7419, # faling
#     1.7422, 1.7437, 1.744, #raising
#     1.7417, #failing
#     #1.7431, 1.7433, #raising
#     #1.7427, #failing
#     #1.7435, 1.7442, #raising
#     #1.7415, #failing
#     #1.7417, 1.7425, 1.7446, #raising
#     #1.7405, #failing
#     #1.7413, 1.742, 1.7422, # raising
#     #1.7387, #failing
#     #1.739, #raising
#     #1.7369, #failing
#     #1.7378, 1.7384, 1.7392, # raising
#     #1.7383, #failing
#     #1.7402, 1.7404, #raising
#     #1.74, 1.7364, 1.733, #failing
#     #1.7333, 1.7335, 1.7365 #raising
#]
#
#async def get_ticker():
#    for data in test_data:
#        #await asyncio.sleep(0.2)
#        yield data

def should_bid(starting_price, current_ticker):
    if add_bidding_percent(starting_price) <= current_ticker:
        return True
    else:
        return False

async def test():
    rising = False
    last_ticker = None
    bid_active = False
    starting_price = -1000
    total_profit = 0.0
    async for current_ticker in get_ticker():
        logger.debug(current_ticker)
        if not last_ticker: # skip first iteration
            last_ticker = current_ticker
            continue
        if current_ticker == last_ticker:
            continue
        if not bid_active and not rising and current_ticker < last_ticker: # still not rising
            last_ticker = current_ticker
            continue

        if rising and current_ticker < last_ticker:
            # start falling
            rising = False
            logger.debug('FALLING')

        if not rising and current_ticker > last_ticker:
            # start rising
            rising = True
            starting_price = last_ticker
            logger.debug('RISING')

        if rising and current_ticker > last_ticker: # still rising
            if not bid_active:
                if should_bid(starting_price, current_ticker):
                    """Bidding here
                    """
                    logger.info(f'BUYING AT {current_ticker}')
                    buying_price = current_ticker
                    bid_active = True


        if bid_active:

            if add_one_percent(buying_price) <= current_ticker:
                total_profit += current_ticker / buying_price - 1
                logger.info('SUCCESS')
                logger.info(f'SELLING AT {current_ticker}')
                logger.info(f'TOTAL PROFIT: {round(total_profit * 100, 2)}%')
                bid_active = False
                buying_price = current_ticker

                starting_price = current_ticker

            if sub_one_percent(buying_price) >= current_ticker:
                total_profit += current_ticker / buying_price - 1
                logger.info('FAILED')
                logger.info(f'SELLING AT {current_ticker}')
                logger.info(f'TOTAL PROFIT: {round(total_profit * 100, 2)}%')
                bid_active = False
                buying_price = current_ticker

                starting_price = current_ticker

        last_ticker = current_ticker

asyncio.get_event_loop().run_until_complete(test())
