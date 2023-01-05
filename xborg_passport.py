import asyncio
import aiohttp

from web3.auto import w3
from loguru import logger
from aiohttp import ClientSession
from random import choice, randint
from aiohttp_proxy import ProxyConnector
from pyuseragents import random as random_useragent


def random_tor_proxy():
    proxy_auth = str(randint(1, 0x7fffffff)) + ':' + \
        str(randint(1, 0x7fffffff))
    proxies = f'socks5://{proxy_auth}@localhost:' + str(choice(tor_port))
    return proxies


def get_connector():
    connector = ProxyConnector.from_url(random_tor_proxy())
    return connector


async def sending_captcha(client: ClientSession):
    try:
        url = 'https://tally.so/'
        site_key = '6LdB13EeAAAAAEQ7MiLZmdG4pa28AD7K4V7x-tgG'
        response = await client.get(f'http://api.captcha.guru/in.php?key={user_key}&method=userrecaptcha \
            &googlekey={site_key}&pageurl={url}')
        data = await response.text()
        if 'ERROR' in data:
            logger.error(print(data))
            return(await sending_captcha(client))
        id = data[3:]
        return(await solving_captcha(client, id))
    except:
        raise Exception()


async def solving_captcha(client: ClientSession, id: str):
    for i in range(100):
        try:
            response = await client.get(f'http://api.captcha.guru/res.php?key={user_key}&action=get&id={id}')
            data = await response.text()
            if 'ERROR' in data:
                logger.error(print(data))
                raise Exception()
            elif 'OK' in data:
                return(data[3:])
            return(await solving_captcha(client, id))
        except:
            raise Exception()
    raise Exception()


def create_wallet():
    account = w3.eth.account.create()
    return(str(account.address), str(account.privateKey.hex()))


def uuid_generate():
    str = '1234567890abcdef'
    text1 = [choice(str) for _ in range(8)]
    text2 = [choice(str) for _ in range(4)]
    text3 = [choice(str) for _ in range(3)]
    text4 = [choice('ab89') for _ in range(1)]
    text5 = [choice(str) for _ in range(12)]
    return(f"{''.join(text1)}-{''.join(text2)}-{'4'+''.join(text3)}-{''.join(text4)+''.join(text3)}-{''.join(text5)}")


async def sending_data(client: ClientSession, email: str, address: str, captcha: str):
    try:
        response = await client.post('https://api.tally.so/forms/w8NJ8z/respond',
                                     json={
                                         "sessionUuid": uuid_generate(),
                                         "respondentUuid": uuid_generate(),
                                         "responses": {
                                             "a7257cab-1f93-4165-894d-ed9e500ddcd6": {
                                                 "10def8d1-5fd8-468b-a396-d4c927e911dc": "website"
                                             },
                                             "acd505ca-7964-4ed9-8fb9-b7d8bc884d28": address,
                                             "6a650868-2999-4208-8261-5d95674019e3": email,
                                             "3667e1d8-46ae-442b-9c08-74a029b57613": [
                                                 "3237f818-02fe-407f-af94-b054028c4ca4",
                                                 "0948069b-8ab8-4e3f-a976-deb5dfcc67cd"
                                             ]
                                         },
                                         "captchas": {
                                             "b9343ab2-71fc-47dd-9db1-31a7b1966c6f": {
                                                 "sitekey": "6LdB13EeAAAAAEQ7MiLZmdG4pa28AD7K4V7x-tgG",
                                                 "response": captcha
                                             }
                                         },
                                         "isCompleted": 'true'
                                     })
        (await response.json())['submissionId']
    except:
        logger.error(await response.json())
        raise Exception()


async def worker(q: asyncio.Queue):
    while True:
        try:
            async with aiohttp.ClientSession(
                connector=get_connector(),
                headers={'user-agent': random_useragent()}
            ) as client:

                logger.info('Get email')
                email = await q.get()

                address, private_key = create_wallet()

                logger.info('Solving captcha')
                captcha = await sending_captcha(client)

                logger.info('Sending data')
                await sending_data(client, email, address, captcha)

        except:
            logger.error('Error\n')
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}:{address}:{private_key}\n')
        else:
            logger.info('Saving data')
            with open('successfully.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}:{address}:{private_key}\n')
            logger.success('Successfully\n')

        await asyncio.sleep(delay)


async def main():
    emails = open("emails.txt", "r+").read().strip().split("\n")
    q = asyncio.Queue()

    for account in list(emails):
        q.put_nowait(account)

    tasks = [asyncio.create_task(worker(q)) for _ in range(threads)]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    tor_port = [9150]

    print("Bot Xborg passport @flamingoat\n")

    user_key = input('Captcha key: ')
    delay = int(input('Delay(sec): '))
    threads = int(input('Threads: '))

    asyncio.run(main())
