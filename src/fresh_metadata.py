from httpx import Timeout, Client, AsyncClient
import time
import asyncio
from config import (
    PROXIES,
    BASEURL,
    CONTRACT,
    ID_TO_REFRESH,
    AMOUNT,
    START_ID,
    OPENSEA_KEY,
)
import regex as re

failed_base_urls = []
failed_image_urls = []
first = True


def ipfs_to_opensea(url: str) -> str:
    """
    convert ipfs url to opensea mypinata url

    Args:
        url (str): ipfs url or other url

    Returns:
        str: mypinata url or not change
    """
    prefix = "ipfs://"
    if url.startswith(prefix):
        hash_and_id = url[len(prefix) :]
        return f"https://opensea.mypinata.cloud/ipfs/{hash_and_id}"
    else:
        return url


def is_base_url(url: str) -> bool:
    """
    check if url is baseurl, end with /numbers

    Args:
        url (str): ipfs url to check

    Returns:
        bool: is base url or not
    """
    regex = r"\/\d+$"
    if re.search(regex, url):
        return True
    else:
        return False


async def ipfs_query(client: AsyncClient, url: str):
    """
    async task for query ipfs

    Args:
        client (AsyncClient): httpx.AsyncClient instance
        url (str): ipfs url to query
    """
    request_url = ipfs_to_opensea(url)
    print(f"url to request: {request_url}")
    is_base = is_base_url(request_url)
    if is_base:
        try:
            metadata_res = await client.get(
                request_url,
                timeout=Timeout(60),
            )
            if metadata_res.status_code == 200:
                if request_url in failed_base_urls:
                    failed_base_urls.remove(request_url)
                    print(f"remove a failed base url, remain: {len(failed_base_urls)}")
                metadata = metadata_res.json()
                image_url = metadata["image"]
                image_opensea_url = ipfs_to_opensea(image_url)
                try:
                    image_res = await client.get(
                        image_opensea_url,
                        timeout=Timeout(60),
                    )
                    if (
                        image_res.status_code == 200
                        and image_opensea_url in failed_image_urls
                    ):
                        failed_image_urls.remove(image_opensea_url)
                        print(
                            f"remove a failed image, remain: {len(failed_image_urls)}"
                        )
                except Exception as e:
                    if image_opensea_url not in failed_image_urls:
                        failed_image_urls.append(image_opensea_url)
                        print(
                            f"add a failed image {image_opensea_url}, number of retries: {len(failed_image_urls)}"
                        )
        except Exception as e:
            if request_url not in failed_base_urls:
                failed_base_urls.append(request_url)
                print(
                    f"add a failed base url {request_url}, number of retries: {len(failed_base_urls)}"
                )
    else:
        try:
            image_res = await client.get(
                request_url,
                timeout=Timeout(60),
            )
            if image_res.status_code == 200 and request_url in failed_image_urls:
                failed_image_urls.remove(request_url)
                print(f"remove a failed image, remain: {len(failed_image_urls)}")
        except Exception as e:
            if request_url not in failed_image_urls:
                failed_image_urls.append(request_url)
                print(
                    f"add a failed image {request_url}, number of retries: {len(failed_image_urls)}"
                )


def opensea_refresh(client: Client, id: int) -> bool:
    """
    task to refresh opensea cache

    Args:
        client (Client): httpx.Client instance
        id (int): nft id

    Returns:
        bool: is success or not
    """
    if OPENSEA_KEY == "":
        print("no opensea key")
        return False
    headers = {
        "Accept": "application/json",
        "X-API-KEY": OPENSEA_KEY,
    }
    request_url = (
        f"https://api.opensea.io/api/v1/asset/{CONTRACT}/{id}/?force_update=true"
    )
    try:
        refresh_res = client.get(request_url, timeout=Timeout(10), headers=headers)
        if refresh_res.status_code == 200:
            print(f"refresh {id} success")
            return True
        else:
            return False
    except Exception as e:
        print(f"refresh {id} fail, url: {request_url}, reason: {e}")
        return False


async def ipfs_query_tasks(request_urls: list[str]):
    """
    create asyncio tasks for ipfs query

    Args:
        request_urls (List[str]): urls to query
    """
    async with AsyncClient(proxies=PROXIES) as client:
        global first
        first = False
        loop = asyncio.get_running_loop()
        tasks = [loop.create_task(ipfs_query(client, url)) for url in request_urls]
        await asyncio.gather(*tasks)


def opensea_refresh_tasks(start_id: int, end_id: int):
    """
    loop task to refresh opensea cache

    Args:
        start_id (int): start nft id
        end_id (int): end nft id
    """

    with Client(proxies=PROXIES) as client:
        failed_id = []
        for id in range(start_id, end_id + 1):
            result = opensea_refresh(client, id)
            if not result:
                failed_id.append(id)
            time.sleep(1)

        while len(failed_id) != 0:
            for id in failed_id:
                result = opensea_refresh(client, id)
                if result:
                    failed_id.remove(id)
            time.sleep(1)


def main(start_id: int, end_id: int):
    """
    use recursive to fresh metadata

    Args:
        start_id (int): start nft id
        end_id (int): end nft id
    """
    global first
    if len(failed_base_urls) == 0 and len(failed_image_urls) == 0 and not first:
        print("no failed urls, time to next batch")
        if OPENSEA_KEY == "":
            print(
                f"""
            no opensea key, 
            go to https://api.opensea.io/api/v1/asset/{CONTRACT}/{start_id}/?force_update=true 
            to refresh manually
            """
            )
        else:
            opensea_refresh_tasks(start_id, end_id)
        first = True
        return

    if first:
        request_urls = []
        if len(ID_TO_REFRESH) == 0:  # full refresh
            for id in range(start_id, end_id + 1):
                request_urls.append(BASEURL + str(id))
        else:
            for id in ID_TO_REFRESH:  # select id refresh
                request_urls.append(BASEURL + str(id))
    else:
        request_urls = failed_base_urls + failed_image_urls
        print("failed urls length:", len(request_urls))

    asyncio.run(ipfs_query_tasks(request_urls))

    wait_time = 60
    print(f"wait {wait_time}s then retry")
    time.sleep(wait_time)

    main(start_id, end_id)


if __name__ == "__main__":
    start = START_ID  # you can change it to process from any id
    amount = AMOUNT + 1
    for start_id in range(start, amount, 100):
        end_id = min(AMOUNT, start_id + 100 - 1)
        print(f"Request {start_id} to {end_id}")
        main(start_id, end_id)
