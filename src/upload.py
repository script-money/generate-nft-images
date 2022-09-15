import asyncio
import os
from typing import Optional, TypedDict, cast
from httpx import (
    AsyncClient,
    Limits,
    Client,
    Response,
)
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
    IPFS_INFO_BACKUP,
)

from final_check import RENAME_DF, START_ID


IPFSInfo = TypedDict("IPFSInfo", {"Name": str, "Hash": str, "Size": str})


class MaxRetryReachException(Exception):
    pass


async def upload_task(
    files_path_chunk: list[str], wait_seconds: float
) -> Optional[list[dict]]:
    """
    upload task for asyncio, a task process 10 files

    Args:
        files_path_chunk (list[str]): a list contain 10 files path
        wait_seconds (float): because infura limit, 1 second can post 10 times, add wait_seconds to wait

    Returns:
        Optional[list[dict]]: 10 files ipfs info
    """
    await asyncio.sleep(wait_seconds)

    async with AsyncClient(
        proxies=PROXIES, limits=Limits(max_keepalive_connections=None), timeout=60
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
        Optional[dict]: ipfs info json
    """
    retry = 0
    max_retries = 3
    while retry <= max_retries:
        try:
            if retry == max_retries:
                raise MaxRetryReachException()
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
            if response.status_code == 403:
                print(f"403 error: {response.content}")
                exit()
            res_json: dict = response.json()
            if res_json["Name"] != "":
                return res_json
        except MaxRetryReachException:
            input("Max retry reach, seems proxy or network error, Press Ctrl+C stop")
        except Exception as e:
            print(f"{file_path.split('-')[0]} {type(e).__name__} error, retry {retry}")
            await asyncio.sleep(retry + 1)
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


def dump_ipfs_info_list_to_local(results: list[IPFSInfo]) -> list[IPFSInfo]:
    """
    dump ipfs info list to local IPFS_INFO_BACKUP

    Args:
        results (list[IPFSInfo]): ipfs info get

    Returns:
        list[IPFSInfo]: ipfs info list to save
    """
    if os.path.exists(IPFS_INFO_BACKUP):
        with open(IPFS_INFO_BACKUP, "r") as f:
            backup_data: list[IPFSInfo] = json.loads(f.read())  # type: ignore
        with open(IPFS_INFO_BACKUP, "w") as g:
            backup_data.extend(results)
            g.write(json.dumps(backup_data))
            print(f"save new {len(backup_data)} ipfs info to local.")
            return backup_data
    else:
        with open(IPFS_INFO_BACKUP, "w") as g:
            g.write(json.dumps(results))
            print(f"save new {len(results)} ipfs info to local.")
            return results


def upload_files(file_paths: list[str]) -> list[IPFSInfo]:
    """
    upload files in a folder to ipfs

    Args:
        folder_name (str): files in folder
        content_type (str, optional): mime file type. Defaults to "image/png".

    Returns:
        list[IPFSInfo]: ipfs info list, example: [{ 'Name': str, 'Hash': str, 'Size': str }]
    """
    file_count = len(file_paths)
    chunk_size = 10  # 10 per second for infura
    chunks = [file_paths[i : i + chunk_size] for i in range(0, file_count, chunk_size)]
    tasks = []
    results: list[IPFSInfo] = []

    def complete_batch_callback(images_ipfs_data):
        ipfs_result: list[IPFSInfo] = images_ipfs_data.result()
        for ipfs_info in ipfs_result:
            results.append(ipfs_info)
        if ipfs_result[0] == None:
            print("No upload info return")
            exit()
        print(f"complete {len(results)/file_count:.2%}")

    loop = asyncio.get_event_loop()
    if file_count == 0:
        print(f"no any images in folder {IMAGES}")
        exit()
    # get average file size in IMAGES folder
    file_size = sum([os.path.getsize(i) for i in file_paths]) / file_count
    epoch_wait: float = file_size / 100000  # 1 second can upload 10 100kB size files
    print(
        f"Total {file_count} files to upload, estimate time: {len(chunks)*epoch_wait+10:.1f}s"
    )  # 200kB per second

    for epoch, path_chunk in enumerate(chunks):
        task = loop.create_task(upload_task(path_chunk, epoch * epoch_wait))
        tasks.append(task)
        task.add_done_callback(complete_batch_callback)

    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        dump_ipfs_info_list_to_local(results)
        exit()
    print(f"upload new {len(results)} files complete.")
    return results


def generate_metadata(
    df: pd.DataFrame,
    image_ipfs_data: list[IPFSInfo],
    start_id: int = 0,
    image_folder: str = IMAGES,
    metadata_folder: str = METADATA,
) -> tuple[int, int]:
    """
    generate metadata for images

    Args:
        df (pd.DataFrame): imagepath and metadata dataframe in final_check.py
        image_ipfs_data (list[IPFSInfo]): image ipfs data from upload_folder
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


def read_images_from_local() -> list[IPFSInfo]:
    """
    read images from local pickle

    Returns:
        list[dict]: images ipfs info
    """
    with open(IPFS_INFO_BACKUP, "r") as f:
        result: list[IPFSInfo] = json.load(f)
        print(f"read {len(result)} ipfs data from local")
        return result


def upload_all_in_image_folder(
    folder_name: str = IMAGES, content_type: str = "image/png"
) -> list[IPFSInfo]:
    """
    upload all files in the folder

    Args:
        folder_name (str, optional): folder name. Defaults to IMAGES.
        content_type (str, optional): content_type header, support png, jpeg, json. Defaults to "image/png".

    Returns:
        list[IPFSInfo]: file upload ipfs info
    """
    extension = content_type.split("/")[-1]
    file_paths = [
        os.path.join(folder_name, file_path)
        for file_path in list(
            filter(lambda i: i.split(".")[-1] == extension, os.listdir(folder_name))
        )
    ]
    new_file_info = upload_files(file_paths)
    # save new ipfs info to local
    dump_ipfs_info_list_to_local(new_file_info)
    return new_file_info


if __name__ == "__main__":
    if not PIN_FILES:
        print(
            f"Pin file is {PIN_FILES}, set PIN_FILES=True in config.py if want to pin files"
        )
    if os.path.exists(IPFS_INFO_BACKUP):
        use_local: str = input(f"{IPFS_INFO_BACKUP} exist, load from local? (y/n)")
        if use_local == "y":
            image_ipfs_data: list[IPFSInfo] = read_images_from_local()
            if image_ipfs_data == None:
                upload_all_in_image_folder()
            else:
                # get file names in IMAGES folder
                image_names: list[str] = [
                    file_name
                    for file_name in os.listdir(IMAGES)
                    if file_name != "attr.csv"
                ]
                # filter image_names not in image_ipfs_data's Name
                images_not_upload: list[str] = list(
                    filter(
                        lambda i: i
                        not in [ipfs_info["Name"] for ipfs_info in image_ipfs_data],  # type: ignore
                        image_names,
                    )
                )
                if len(images_not_upload) != 0:
                    confirm_upload: str = input(
                        f"found {len(images_not_upload)} files are not uploaded, press 'y' to upload (y/n)"
                    )
                    if confirm_upload == "y" or confirm_upload == "Y":
                        images_path_not_upload = list(
                            map(lambda i: os.path.join(IMAGES, i), images_not_upload)
                        )
                        new_file = upload_files(images_path_not_upload)
                        image_ipfs_data = dump_ipfs_info_list_to_local(new_file)

                    else:
                        exit()
        else:
            image_ipfs_data: list[IPFSInfo] = upload_all_in_image_folder()
    else:
        image_ipfs_data: list[IPFSInfo] = upload_all_in_image_folder()

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
