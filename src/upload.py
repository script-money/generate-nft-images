from dotenv import load_dotenv
import os
import requests as rq
import json
from get_table import IMAGES, METADATA, NAME, DESCRIPTION
import pandas as pd
import numpy as np
from final_check import RENAME_DF
from cid import make_cid

load_dotenv()

PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

# Load upload configuration, need to register ipfs of infura to get PROJECT_ID and PROJECT_SECRET
PROJECT_ID = os.getenv("PROJECT_ID")
PROJECT_SECRET = os.getenv("PROJECT_SECRET")


def upload_folder(
    folder_name: str, content_type: str = "image/png"
) -> tuple[str, list[dict]]:
    files = []
    if content_type == "image/png":
        files = [
            (
                folder_name.split("/")[-1],
                (file, open(os.path.join(folder_name, file), "rb"), content_type),
            )
            for file in list(
                filter(lambda i: i.split(".")[-1] == "png", os.listdir(folder_name))
            )
        ]
    elif content_type == "application/json":
        files = [
            (
                folder_name.split("/")[-1],
                (file, open(os.path.join(folder_name, file), "rb"), content_type),
            )
            for file in list(filter(lambda i: "." not in i, os.listdir(folder_name)))
        ]
    response = rq.post(
        f"https://ipfs.infura.io:5001/api/v0/add?pin=false&recursive=true&wrap-with-directory=true",
        files=files,
        auth=(PROJECT_ID, PROJECT_SECRET),
        proxies=PROXIES,
    )

    upload_folder_res_list = response.text.split("\n")
    assert len(files) + 2 == len(
        upload_folder_res_list
    ), f"Different number of successfully uploaded files and folders, \
      need {len(files)+2}, return {len(upload_folder_res_list)}"
    try:
        folder_hash = json.loads(
            [
                i
                for i in upload_folder_res_list
                if i != "" and json.loads(i)["Name"] == ""
            ][0]
        )["Hash"]
    except:
        folder_hash = None
    images_dict_list = [
        json.loads(i)
        for i in upload_folder_res_list
        if i != "" and json.loads(i)["Name"] != ""
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
        imagehash = row["imagehash"]
        index = idx + start_count
        if imagehash == None:
            print(path)
            image_dict = next(
                filter(
                    lambda i: os.path.join(image_folder, i["Name"]) == path,
                    image_ipfs_data,
                ),
                None,
            )
            df.loc[idx, "imagehash"] = image_dict["Hash"]
            cols = list(df.columns)[2:]
            attributes = [{"value": col, "trait_type": row[col]} for col in cols]
            cidv1 = (
                make_cid(image_dict["Hash"]).to_v1().encode("base32").decode("UTF-8")
            )  # convert cidv1 reduce image load time
            info_dict = {
                "name": f"{NAME} #{index}",
                "description": f"{DESCRIPTION}",
                "image": f"https://{cidv1}.ipfs.dweb.link/",
                "attributes": attributes,
            }
            info_json = json.dumps(info_dict)
            with open(os.path.join(metadata_folder, str(index)), "w") as f:
                f.write(info_json)
        else:
            print(f"row {idx} has image hash, skip")
    print(f"save metadata complete")

    meta_root, _ = upload_folder(metadata_folder, "application/json")
    print(f"upload metadatas complete")
    return (meta_root, start_count, start_count + len(df))


if __name__ == "__main__":
    df = RENAME_DF
    image_ipfs_root, image_ipfs_data = upload_folder(IMAGES)
    print(f"image_ipfs_root: {image_ipfs_root}")
    print(f"image_ipfs_data: {image_ipfs_data}")
    tokenurl_hash, start, end = generate_metadata_and_upload(
        df, image_ipfs_root, image_ipfs_data
    )
    print(
        f"Source url is {tokenurl_hash}, you can visit ipfs://{tokenurl_hash}/{start} to check"
    )
    print(f"Index from {start} to {end}")
    print(f"Or visit https://cloudflare-ipfs.com/ipfs/{tokenurl_hash}/{start}")
    print("May take some times load page")
