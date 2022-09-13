import os
import httpx
import json
from config import (
    IMAGES,
    METADATA,
    NAMES,
    DESCRIPTION,
    PROJECT_ID,
    PROJECT_SECRET,
    PROXIES,
    READ_IMAGES,
    UPLOAD_METADATA,
    PIN_FILES,
)
import pandas as pd
from final_check import RENAME_DF, START_ID
import random


def upload_folder(
    folder_name: str, content_type: str = "image/png"
) -> tuple[str, list[dict]]:
    """
    upload folder to ipfs

    Args:
        folder_name (str): folder name to upload
        content_type (str, optional): mime file type. Defaults to "image/png".

    Returns:
        tuple[str, list[dict]]: (folder_hash, images_dict_list)
    """
    files = []
    if content_type == "image/png":
        files = [
            (
                folder_name.split(os.sep)[-1],
                (file, open(os.path.join(folder_name, file), "rb"), content_type),
            )
            for file in list(
                filter(lambda i: i.split(".")[-1] == "png", os.listdir(folder_name))
            )
        ]
    elif content_type == "image/gif":
        files = [
            (
                folder_name.split(os.sep)[-1],
                (file, open(os.path.join(folder_name, file), "rb"), content_type),
            )
            for file in list(
                filter(lambda i: i.split(".")[-1] == "gif", os.listdir(folder_name))
            )
        ]
    elif content_type == "application/json":
        files = [
            (
                folder_name.split(os.sep)[-1],
                (file, open(os.path.join(folder_name, file), "rb"), content_type),
            )
            for file in list(filter(lambda i: "." not in i, os.listdir(folder_name)))
        ]

    with httpx.Client(proxies=PROXIES, timeout=None) as client:
        response = client.post(
            f"https://ipfs.infura.io:5001/api/v0/add?pin={'true' if PIN_FILES else 'false'}&recursive=true&wrap-with-directory=true",  # pin=true if want to pin files
            files=files,
            auth=(PROJECT_ID, PROJECT_SECRET),
        )
        upload_folder_res_list = response.text.strip().split("\n")
        if (
            upload_folder_res_list[0]
            == "basic auth failure: invalid project id or project secret"
        ):
            assert False, "invalid project id or project secret"
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


def generate_metadata(
    df: pd.DataFrame,
    image_ipfs_data: dict,
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
    for idx, row in df.iterrows():
        path = row["path"]
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
        with open(os.path.join(metadata_folder, str(index)), "w") as f:
            f.write(info_json)

    return (start_id, start_id + len(df) - 1)


if __name__ == "__main__":
    df = RENAME_DF
    if not READ_IMAGES:
        image_ipfs_root, image_ipfs_data = upload_folder(IMAGES)
        print(f"image_ipfs_root: {image_ipfs_root}")
        # backup file use for debug upload images data
        with open("image_ipfs_data.backup", "w") as f:
            f.write(json.dumps(image_ipfs_data))
        print("save image_ipfs_data to image_ipfs_data.backup")
    else:
        # if read images hashes from backup
        with open("image_ipfs_data.backup", "r") as j:
            image_ipfs_data = json.loads(j.read())

    start, end = generate_metadata(df, image_ipfs_data, START_ID)
    print(f"Generate metadata complete, Index from {start} to {end}")

    if UPLOAD_METADATA:
        print("uploading metadata")
        metadata_root, _ = upload_folder(METADATA, "application/json")
        print(f"upload metadatas complete")
        print(
            f"Source url is {metadata_root}, you can visit ipfs://{metadata_root}/{start} to check"
        )
