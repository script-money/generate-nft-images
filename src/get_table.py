import os
from PIL import Image
import pandas as pd
import shutil
from config import FOLDERS, EXTENSION, W, H, WEIGHTS, LAYER_NAMES
from math import fsum


def get_files_path(folders=FOLDERS):
    """
    helper function to get source layer files path

    Args:
        folders (str, optional): root folder save source layer files. Defaults to FOLDERS.

    Returns:
        List[str]: all source layer files path
    """
    files_path = []
    for folder in folders:
        assert os.path.exists(
            folder
        ), f"{folder} folder does not exist, please check PARTS_DICT in config.py"
        for root, _, _ in os.walk(folder):
            if root not in FOLDERS:
                for _, _, files in os.walk(root):
                    assert (
                        len(files) > 0
                    ), f"{root} is empty, if you don't want to use this trait, please add an empty.png in this folder"
                    for file in files:
                        if file != ".DS_Store":
                            files_path.append(os.path.join(root, file))
    files_path.sort()
    return files_path


files_path = get_files_path()

if __name__ == "__main__":
    # clean old folder
    folders = ["images", "metadata"]
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"{folder} folder cleaned")
        os.mkdir(folder)

    # Validate weights
    assert (
        fsum(WEIGHTS) == 1
    ), f"sum of PARTS_DICT's value in config.py should be 1, now is {sum(WEIGHTS)}"

    # Validate image format and size
    error = 0
    for path in files_path:
        try:
            assert (
                path.split(".")[-1] in EXTENSION
            ), f"{path}'s extension is not {EXTENSION} "
            im = Image.open(path)
            w, h = im.size
            assert w == W, f"{path} width not equal {W}"
            assert h == H, f"{path} height not equal {H}"
        except Exception as e:
            print(e)
            error += 1
    if error != 0:
        print(f"{error} images have error, fix and try again")
        exit()

    # Validate path name has -
    for path in files_path:
        assert (
            "-" not in path.split(os.sep)[-1]
        ), f"{path} is invalid, files should not have '-' symbol"

    folder_set = set()
    folder_error = 0
    # check all parts folders has same order
    for folder in FOLDERS:
        try:
            for root, subfolders, _ in os.walk(folder):
                if root == folder:
                    for subfolder in subfolders:
                        if subfolder not in folder_set and subfolder.split("_")[
                            1
                        ] in map(lambda f: f.split("_")[1], folder_set):
                            raise Exception(
                                f"in '{root}' folder '{subfolder}' is invalid, index of subfolder with same trait should be same."
                            )
                        else:
                            folder_set.add(subfolder)
        except Exception as e:
            print(e)
            folder_error += 1
    if folder_error != 0:
        print("Exited, please fix subfolder error and retry")
        exit()

    # export tables
    attrs = [os.path.split(path) for path in files_path]
    first_prop_info = (
        str(attrs[0][0].split(os.sep)[-1].split("_")[1])
        + " : "
        + str(attrs[0][1].split(".")[0])
    )
    second_prop_info = (
        str(attrs[1][0].split(os.sep)[-1].split("_")[1])
        + " : "
        + str(attrs[1][1].split(".")[0])
    )
    # create empty.png
    if not os.path.exists("empty.png"):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        im.save("empty.png")

    # fill empty to miss folders, split attrs to multiple parts by folder
    for subfolder in FOLDERS:
        layer_names = LAYER_NAMES
        if len(layer_names) == 0:
            layer_names = list(sorted(set(map(lambda i: i[0].split(os.sep)[1], attrs))))

        use_prop_filter_by_folder = list(
            filter(lambda i: i[0].split(os.sep)[0] == subfolder, attrs)
        )
        use_prop = set(map(lambda i: i[0].split(os.sep)[1], use_prop_filter_by_folder))
        remain_prop = set(layer_names) - use_prop
        for add_prop in remain_prop:
            folder_to_create = f"{subfolder}/{add_prop}"
            os.mkdir(folder_to_create)
            shutil.copy("empty.png", folder_to_create)
            attrs.append((folder_to_create, "empty.png"))

    ratio_data = {
        "folder": [a[0].split(os.sep)[0] for a in attrs],
        "prop": [a[0].split("_")[1] for a in attrs],
        "value": [a[1].split(".")[0] for a in attrs],
        "ratio": 1,
    }
    df0 = pd.DataFrame(data=ratio_data)
    df0.to_csv("ratio.csv", index=False)
    rule_data = {
        "prop": [a[0].split("_")[1] for a in attrs],
        "value": [a[1].split(".")[0] for a in attrs],
        "list_prop_value": "",
        "rule": 0,
    }
    df1 = pd.DataFrame(data=rule_data)
    print("---example rules---")
    *other, prop_1, prop_2 = df1["prop"].unique()
    value1 = df1[df1["prop"] == prop_1]["value"].unique()[0]
    value2 = df1[df1["prop"] == prop_2]["value"].unique()[0]
    df1.loc[0, "list_prop_value"] = f"[('{prop_1}','{value1}'),('{prop_2}','{value2}')]"
    print(
        f"if prop is {first_prop_info}, attrs will have [('{prop_1}','{value1}'),('{prop_2}','{value2}')] "
    )
    df1.loc[1, "list_prop_value"] = f"[('{prop_1}','{value1}')]"
    print(
        f"if prop is {second_prop_info}, attrs will NOT have [('{prop_1}','{value1}')]"
    )
    df1.loc[0, "rule"] = 1
    df1.loc[1, "rule"] = -1
    df1.to_csv("rules.csv", index=False)
    print("set your rules in rules.csv")
    print("-------------------")
    if os.path.exists("ratio.csv"):
        print("generate table success!")
        print("You can modify ratio.csv to change the ratio of each parts")
        print("PS: Don't use Excel to save csv, use notepad instead")
