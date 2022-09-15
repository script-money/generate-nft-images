import asyncio
import os
from typing import Optional, cast
from httpx import AsyncClient, Limits, ReadTimeout, Client, ConnectError, Response
import json
import pandas as pd
import random
from config import (
    IMAGES,
    METADATA,
    NAMES,
    DESCRIPTION,
    PROJECT_ID,
    PROJECT_SECRET,
    PROXIES,
    UPLOAD_METADATA,
    PIN_FILES,
)
from final_check import RENAME_DF, START_ID


async def upload_task(
    files_path_chunk: list[str], wait_seconds: int
) -> Optional[list[dict]]:
    """
    upload task for asyncio, a task process 10 files

    Args:
        files_path_chunk (list[str]): a list contain 10 files path
        wait_seconds (int): because infura limit, 1 second can post 10 times, add wait_seconds to wait

    Returns:
        list[dict]: 10 files ipfs info
    """
    await asyncio.sleep(wait_seconds)
    async with AsyncClient(
        proxies=PROXIES, limits=Limits(max_connections=10), timeout=60
    ) as client:
        loop = asyncio.get_running_loop()
        tasks = [
            loop.create_task(upload_single_async(client, file_path))
            for file_path in files_path_chunk
        ]
        result = await asyncio.gather(*tasks)
        if all(map(lambda i: i is None, result)):
            return None
        return result


async def upload_single_async(client: AsyncClient, file_path: str) -> Optional[dict]:
    """
    upload folder to ipfs

    Args:
        client (AsyncClient): httpx.asyncClient instance
        file_path (str): path of file want to upload

    Returns:
        dict: ipfs info json
    """
    retry = 0
    while retry < 5:
        try:
            response: Response = await client.post(
                f"https://ipfs.infura.io:5001/api/v0/add",
                params={
                    "pin": "true" if PIN_FILES else "false"
                },  # pin=true if want to pin files
                auth=(PROJECT_ID, PROJECT_SECRET),  # type: ignore
                files={"file": open(file_path, "rb")},
            )
            if response.status_code == 401:
                print("Project ID and scecret is invalid")
                exit()
            res_json: dict = response.json()
            if res_json["Name"] != "":
                return res_json
        except Exception as e:
            if isinstance(e, ReadTimeout):
                print(f"upload {file_path.split('-')[0]} timeout, retry {retry}")
            elif isinstance(e, ConnectError):
                print(f"can't connect to ipfs, please check network or proxy setting")
                exit()
            else:
                print(f"upload {file_path.split('-')[0]} error, exit")
                exit()
            retry += 1
    return None


def upload_folder(
    folder_name: str, content_type: str = "image/png"
) -> tuple[Optional[str], Optional[list[dict]]]:
    """
    upload folder to ipfs

    Args:
        folder_name (str): folder name to upload
        content_type (str, optional): mime file type. Defaults to "image/png".

    Returns:
        tuple[Optional[str], Optional[list[dict]]]: (folder_hash, images_dict_list)
    """
    files = []
    extension = content_type.split("/")[-1]

    files = [
        (file, open(os.path.join(folder_name, file), "rb"))
        for file in list(
            filter(lambda i: i.split(".")[-1] == extension, os.listdir(folder_name))
        )
    ]

    with Client(proxies=PROXIES, timeout=None) as client:
        response = client.post(
            f"https://ipfs.infura.io:5001/api/v0/add",
            params={
                "pin": "true" if PIN_FILES else "false",
                "recursive": "true",
                "wrap-with-directory": "true",
            },
            files=files,  # files should be List[filename, bytes]
            auth=(PROJECT_ID, PROJECT_SECRET),  # type: ignore
        )
        upload_folder_res_list = response.text.strip().split("\n")
        if (
            upload_folder_res_list[0]
            == "basic auth failure: invalid project id or project secret"
        ):
            assert False, "invalid project id or project secret"
        folder_hash: Optional[str] = ""
        try:
            folder_hash = json.loads(
                [i for i in upload_folder_res_list if json.loads(i)["Name"] == ""][0]
            )["Hash"]
        except:
            folder_hash = None
        images_dict_list = [
            json.loads(i) for i in upload_folder_res_list if json.loads(i)["Name"] != ""
        ]
        return (folder_hash, images_dict_list)


def upload_files(folder_name: str, content_type: str = "image/png") -> list[dict]:
    """
    upload files in a folder to ipfs

    Args:
        folder_name (str): files in folder
        content_type (str, optional): mime file type. Defaults to "image/png".

    Returns:
        list[dict]: ipfs info list, example: [{ 'Name': str, 'Hash': str, 'Size': str }]
    """
    extension = content_type.split("/")[-1]
    file_paths = [
        os.path.join(folder_name, file_path)
        for file_path in list(
            filter(lambda i: i.split(".")[-1] == extension, os.listdir(folder_name))
        )
    ]
    file_count = len(file_paths)
    chunk_size = 10  # 10 per second for infura
    chunks = [file_paths[i : i + chunk_size] for i in range(0, file_count, chunk_size)]
    tasks = []
    results = []

    def complete_batch_callback(images_ipfs_data):
        results.append(images_ipfs_data.result())
        if results[0] == None:
            print("No upload info return")
            exit()
        print(f"complete {len(results)/len(chunks):.2%}")

    loop = asyncio.get_event_loop()
    if file_count == 0:
        print(f"no any images in folder {IMAGES}")
        exit()
    print(f"Total {file_count} files to upload, estimate time: {len(chunks)+10}s")
    for epoch, path_chunk in enumerate(chunks):
        task = loop.create_task(upload_task(path_chunk, epoch))
        tasks.append(task)
        task.add_done_callback(complete_batch_callback)

    loop.run_until_complete(asyncio.wait(tasks))
    print(f"upload {len(results)} files complete.")
    return results


def generate_metadata(
    df: pd.DataFrame,
    image_ipfs_data: list[dict],
    start_id: int = 0,
    image_folder: str = IMAGES,
    metadata_folder: str = METADATA,
) -> tuple[int, int]:
    """
    generate metadata for images

    Args:
        df (pd.DataFrame): imagepath and metadata dataframe in final_check.py
        image_ipfs_data (dict): image ipfs data from upload_folder
        start_id (int, optional): start index. Defaults to 0.
        image_folder (str, optional): images folder to use compare. Defaults to IMAGES.
        metadata_folder (str, optional): metadata save folder. Defaults to METADATA.

    Returns:
        tuple[int, int]: (start_id, end_id)
    """
    index: Optional[int]
    for idx, row in df.iterrows():
        path = row["path"]
        idx = cast(int, idx)
        index = idx + start_id
        image_dict = next(
            filter(
                lambda i: os.path.join(image_folder, i["Name"]) == path,
                image_ipfs_data,
            ),
            None,
        )
        if image_dict == None:
            print(f"{path} not found in ipfs")
            continue
        cols = list(df.columns)[1:]  # exclude index
        attributes = [
            {"value": row[col], "trait_type": col}
            for col in cols
            if row[col] != "empty"
        ]
        hash = image_dict["Hash"]

        info_dict = {
            "name": f"{random.choice(NAMES)} #{index}",
            "description": f"{DESCRIPTION}",
            "image": f"ipfs://{hash}/",
            "attributes": attributes,
        }
        info_json = json.dumps(info_dict)
        with open(os.path.join(metadata_folder, str(index) + ".json"), "w") as f:
            f.write(info_json)

    return (start_id, start_id + len(df) - 1)


def read_images_from_local() -> list[dict]:
    """
    read images from local pickle

    Returns:
        list[dict]: images ipfs info
    """
    with open("image_ipfs_data.backup", "r") as f:
        result: list[dict] = json.loads(f.read())
        print(f"read {len(result)} ipfs data from local")
        return result


def download_and_save():
    """
    upload images and get ipfs info

    Returns:
        list[dict]: images ipfs info
    """
    all_ipfs_info_batch = upload_files(IMAGES)
    image_ipfs_data = []
    for batch_info in all_ipfs_info_batch:
        for single_info in batch_info:
            image_ipfs_data.append(single_info)
    with open("image_ipfs_data.backup", "w") as f:
        f.write(json.dumps(image_ipfs_data))
    print("save image_ipfs_data to image_ipfs_data.backup")
    return image_ipfs_data


if __name__ == "__main__":
    if not PIN_FILES:
        print(
            f"Pin file is {PIN_FILES}, set PIN_FILES=True in config.py if want to pin files"
        )
    if os.path.exists("image_ipfs_data.backup"):
        use_local = input("image_ipfs_data.backup exist, load from local? (y/n)")
        if use_local == "y":
            image_ipfs_data = read_images_from_local()
        else:
            image_ipfs_data = download_and_save()
    else:
        image_ipfs_data = download_and_save()

    df = RENAME_DF
    start, end = generate_metadata(df, image_ipfs_data, START_ID)
    print(f"Generate metadata complete, Index from {start} to {end}")

    if UPLOAD_METADATA:
        print("uploading metadata")
        metadata_root, _ = upload_folder(METADATA, "application/json")
        print(f"upload metadatas complete")
        print(
            f"Source url is {metadata_root}, you can visit ipfs://{metadata_root}/{start}.json to check"
        )
