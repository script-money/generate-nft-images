import os
from PIL import Image
import pandas as pd
import numpy as np
import random
from numpy.random import choice
from get_table import files_path
from pathlib import Path
from config import (
    W,
    H,
    PARTS_DICT,
    FOLDERS,
    WEIGHTS,
    IMAGES,
    QUALITY,
    AMOUNT,
    START_ID,
    EXTENSION,
    ROOT_DIR,
)
from multiprocessing import Pool, cpu_count


def random_attr():
    """
    helper function to generate random attributes

    Returns:
        List: [{"value": value, "trait_type": prop}]
    """
    attributes = []
    select_folder = choice(FOLDERS, p=WEIGHTS)
    for prop in props:
        k = random.random()
        ratio_arr = df_pac.query(
            f"(folder == '{select_folder}') & (prop == '{prop}')"
        ).ratio.values
        cum_arr = np.cumsum(ratio_arr) - k
        first_index = next(x[0] for x in enumerate(cum_arr) if x[1] > 0)
        value = df_pac.loc[(select_folder), (prop), :].index[
            first_index
        ]  # in pandas 1.4, loc is not return tuple but single element
        if type(value) is str:
            attributes.append(
                {"value": (select_folder, prop, value), "trait_type": prop}
            )
        else:
            attributes.append({"value": value, "trait_type": prop})
    return attributes


def get_ratio(x):
    """
    helper function to get ratio of each folder

    Args:
        x (DataFrame): dataframe containing folder and ratio

    Returns:
          float: possibility of each trait
    """
    folder_name = x["folder"].values[0]
    custom_ratio = x["ratio"].values[0]
    folder_ratio = PARTS_DICT[folder_name]
    return custom_ratio * folder_ratio


def has_transparency(img):
    if img.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False


def generate_func(
    start_index, end_index, start_id=0,
):
    """
    generate images function single process

    Args:
        start_index (_type_): start index
        end_index (_type_): end index
        start_id (int, optional): which index start. Defaults to 0.

    Returns:
        pd.DataFrame: generated dataframe by this process
    """
    cols = ["path"] + [i["trait_type"] for i in random_attr()]
    df_batch = pd.DataFrame(columns=cols)
    for i in range(start_index, end_index):
        # avoid duplicate
        index = i + start_id
        attributes = random_attr()
        key = hash(str(attributes))
        while key in used_attributes:
            attributes = random_attr()
            key = hash(str(attributes))
        used_attributes[key] = attributes
        # Get the images to be read in the order of overlay
        paths = [
            next(
                path
                for path in files_path
                if attr["trait_type"] == path.split(os.sep)[1].split("_")[1]
                and attr["value"][0] == path.split(os.sep)[0]
                and attr["value"][2] == Path(path).stem
            )
            for attr in attributes
        ]
        base_img = Image.new("RGB", (W, H), (0, 0, 0))
        for path in paths:
            img = Image.open(path, "r")
            if not has_transparency(img):
                img = img.convert("RGBA")
            base_img.paste(img, (0, 0), mask=img)
        # save images
        filename = (
            f"{index}-{'-'.join(list(map(lambda i: i['value'][-1] ,attributes)))}.png"
        )
        base_img.save(
            os.path.join(save_folder, filename), format="jpeg", quality=QUALITY,
        )
        # add porpety
        row_dict = {"path": os.path.join(save_folder, filename)} | {
            i["trait_type"]: i["value"][-1] for i in attributes
        }
        new_row_df = pd.DataFrame.from_dict(row_dict, orient="index").T
        df_batch = pd.concat([df_batch, new_row_df], ignore_index=True,)
    return df_batch


def generate_images(
    df_csv: pd.DataFrame, amount: int, save_folder: str = "./images", start_id: int = 0,
) -> pd.DataFrame:
    """
    generate images main function, check prequisites and generate images in parallel

    Args:
        df_csv (pd.DataFrame): source dataframe to use
        amount (int): image amount to generate
        save_folder (str, optional): images save folder. Defaults to "./images".
        start_id (int, optional): which index start. Defaults to 0.

    Returns:
        pd.DataFrame: all generated images with save to attr.csv and return
    """
    prop_count_df = df_csv.groupby(["folder", "prop"]).count()
    sum_count = 0
    for _folder in FOLDERS:
        folder_df = prop_count_df.query(f"folder == '{_folder}'")["ratio"]
        max_count = folder_df.values.cumprod()[-1]
        sum_count += max_count
    assert (
        amount <= sum_count
    ), "Generate too much, there will be duplicate generation, should increase the number of material or reduce the total amount"
    min_ratio_except_zero = np.min(df_pac[df_pac["ratio"] > 0].ratio.values)
    assert (
        min_ratio_except_zero * amount >= 1
    ), "The number generated is too small to reflect the minimum probability and the total should be increased"
    assert (
        len(list(filter(lambda f: f.split(".")[1] == "png", os.listdir(save_folder))))
        == 0
    ), f"{save_folder} folder is not empty, backup the original data and tables first"

    processes = cpu_count() - 1
    pool = Pool(processes=processes)
    start_end_indexs = list(
        map(
            lambda x: (
                x * amount // processes,
                (x + 1) * amount // processes,
                start_id,
            ),
            range(processes),
        )
    )

    df_attr = pool.starmap(generate_func, start_end_indexs)
    pd.concat(df_attr, ignore_index=True).to_csv(
        os.path.join(save_folder, "attr.csv"), index=False
    )
    return df_attr


def check_values_valid(df: pd.DataFrame, select_columns: list, all_values: list):
    """
    Check selected column values is in the list

    Args:
        df (pd.DataFrame): DataFrame to check
        select_columns (List): columns to check
        all_values (List): possible values

    Raises:
        ValueError: if data invalid (is not in all_values)
    """
    values_to_check_df = df[list(select_columns)]
    all_values = list(df_group.index.levels[2])
    # loop rows if the value is not in the all_values, raise error
    for i, row in values_to_check_df.iterrows():
        for prop in props:
            if row[prop] not in all_values:
                raise ValueError(
                    f'"{row[prop]}" is not valid prop at row "{i}" & column "{prop}"'
                )


def generate_images_from_attr_csv(csv_path: str):
    """ 
    This function use for modify same images already generated
    You should use attr.csv in images folder as csv_path
    Change some value in csv then run this function

    Args:
        csv_path (str): use attr.csv in images folder
    """
    modified_csv = pd.read_csv(csv_path)
    all_values = list(df_group.index.levels[2])
    check_values_valid(modified_csv, props, all_values)
    df_batch = pd.DataFrame()
    assert (
        len(list(filter(lambda f: f.split(".")[1] == "png", os.listdir(save_folder))))
        == 0
    ), f"{save_folder} folder is not empty, backup the original data and tables first"

    # loop modified_csv and generate images
    for index, row in modified_csv.iterrows():
        attributes = []
        base_img = Image.new("RGB", (W, H), (0, 0, 0))
        for prop_index, prop in enumerate(props):
            for folder in FOLDERS:
                for ext in EXTENSION:
                    path = os.path.join(
                        ROOT_DIR,
                        folder,
                        f"0{prop_index+1}_{prop}",
                        f"{row[prop]}.{ext}",
                    )

                    if os.path.exists(path):
                        img = Image.open(path, "r")
                        if not has_transparency(img):
                            img = img.convert("RGBA")
                        base_img.paste(img, (0, 0), mask=img)
                        if (prop_index, row[prop],) not in attributes:
                            attributes.append((prop_index, row[prop]))
        # save images
        filename = f"{index}-{'-'.join(map(lambda t: t[1],attributes))}.png"
        save_path = os.path.join(save_folder, filename)
        base_img.save(save_path, format="jpeg", quality=QUALITY)
        # add porpety
        row_dict = {"path": save_path} | {prop: row[prop] for prop in props}
        new_row_df = pd.DataFrame.from_dict(row_dict, orient="index").T
        df_batch = pd.concat([df_batch, new_row_df], ignore_index=True,)

    df_batch.to_csv(os.path.join(save_folder, "attr.csv"), index=False)


df_csv = pd.read_csv("./ratio.csv")
df_group = df_csv.groupby(["folder", "prop", "value"]).apply(get_ratio).to_frame()
df_pac = (
    df_group.groupby(level=["folder", "prop"])
    .apply(lambda x: x / float(x.sum()))
    .rename(columns={0: "ratio"})
)
props = df_csv["prop"].unique()
used_attributes = {}
save_folder: str = IMAGES


if __name__ == "__main__":
    print(f"generating/... check images in {save_folder} folder")
    print(f"quality is {QUALITY}")
    print("PS: you can press Ctrl+C to stop the process")
    generate_images(df_csv, AMOUNT, start_id=START_ID)
    print(f"generate {AMOUNT} images in {save_folder} folder success")

    # if you want to modify images already generated, use this function
    # generate_images_from_attr_csv('images/attr.csv')
