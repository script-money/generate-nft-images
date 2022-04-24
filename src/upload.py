import os
import requests as rq
import json
from get_table import (
    IMAGES,
    METADATA,
    NAMES,
    DESCRIPTION,
    PROXIES,
    PROJECT_ID,
    PROJECT_SECRET,
)
import pandas as pd
from final_check import RENAME_DF, START_ID
from cid import make_cid
import random


def upload_folder(
    folder_name: str, content_type: str = "image/png"
) -> tuple[str, list[dict]]:
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
    response = rq.post(
        f"https://ipfs.infura.io:5001/api/v0/add?pin=true&recursive=true&wrap-with-directory=true",  # pin=true if want to pin files
        files=files,
        auth=(PROJECT_ID, PROJECT_SECRET),
        proxies=PROXIES,
    )

    upload_folder_res_list = response.text.strip().split("\n")
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


def generate_metadata_and_upload(
    df: pd.DataFrame,
    image_ipfs_data: dict,
    start_count: int = 0,
    image_folder: str = IMAGES,
    metadata_folder: str = METADATA,
) -> tuple[str, int, int]:
    for idx, row in df.iterrows():
        path = row["path"]
        index = idx + start_count
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

        cidv1 = (
            make_cid(image_dict["Hash"]).to_v1().encode("base32").decode("UTF-8")
        )  # convert cidv1 reduce image load time

        info_dict = {
            "name": f"{random.choice(NAMES)} #{index}",
            "description": f"{DESCRIPTION}",
            "image": f"https://{cidv1}.ipfs.dweb.link/",
            "attributes": attributes,
        }
        info_json = json.dumps(info_dict)
        with open(os.path.join(metadata_folder, str(index)), "w") as f:
            f.write(info_json)

    print(f"save metadata complete")

    meta_root, _ = upload_folder(metadata_folder, "application/json")
    print(f"upload metadatas complete")
    return (meta_root, start_count, start_count + len(df) - 1)


if __name__ == "__main__":
    df = RENAME_DF
    image_ipfs_root, image_ipfs_data = upload_folder(IMAGES)
    print(f"image_ipfs_root: {image_ipfs_root}")
    # backup file use for debug upload images data
    with open("image_ipfs_data.backup", "w") as f:
        f.write(json.dumps(image_ipfs_data))
    print("save image_ipfs_data to image_ipfs_data.backup")
    tokenurl_hash, start, end = generate_metadata_and_upload(
        df, image_ipfs_data, START_ID
    )
    print(
        f"Source url is {tokenurl_hash}, you can visit ipfs://{tokenurl_hash}/{start} to check"
    )
    print(f"Index from {start} to {end}")
