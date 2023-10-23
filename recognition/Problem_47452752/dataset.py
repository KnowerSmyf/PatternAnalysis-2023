"""
File containing the data loaders used for loading and preprocessing the data.

"""

import os
import torch
from utils import RandomCenterCrop, RandomRotate90, DictTransform
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.dataset import random_split
from torchvision import transforms
import torchvision.transforms.functional as TF
from PIL import Image
import numpy as np


class ISICDataset(Dataset):
    def __init__(
        self,
        image_dir,
        mask_dir,
        transform=None,
    ):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.image_ids = [img.split(".")[0] for img in os.listdir(image_dir)]
        self.transform = transform

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_name = os.path.join(self.image_dir, self.image_ids[idx] + ".jpg")
        mask_name = os.path.join(
            self.mask_dir, self.image_ids[idx] + "_Segmentation.png"
        )

        if not os.path.exists(img_name) or not os.path.exists(mask_name):
            raise FileNotFoundError(
                f"Image or mask not found for ID {self.image_ids[idx]}"
            )

        with image.open(img_name) as image, Image.open(mask_name) as mask:
            image = image.convert("RGB")
            mask = mask.convert("L")

            sample = {"image": image, "mask": mask}

            if self.transform:
                sample = self.transform(sample)

        # Convert mask to binary 0/1 tensor
        sample["mask"] = (torch.tensor(np.array(sample["mask"])) > 127.5).float()

        return sample["image"], sample["mask"]


# Transformation pipeline to augment the dataset
transform = transforms.Compose(
    [
        RandomRotate90(),
        RandomCenterCrop(),
        DictTransform(transforms.RandomHorizontalFlip()),
        DictTransform(transforms.RandomVerticalFlip()),
        DictTransform(transforms.Resize((256, 256))),
        DictTransform(transforms.ToTensor()),
        DictTransform(transforms.Lambda(lambda img_tensor: torch.cat([img_tensor, TF.to_tensor(TF.to_pil_image(img_tensor).convert("HSV"))], dim=0)), False),
        DictTransform(transforms.Normalize([0.5, 0.5, 0.5, 0.5, 0.5, 0.5], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]), False),
    ]
)

image_dir = "/home/groups/comp3710/ISIC2018/ISIC2018_Task1-2_Training_Input_x2"
mask_dir = "/home/groups/comp3710/ISIC2018/ISIC2018_Task1_Training_GroundTruth_x2"

dataset = ISICDataset(image_dir, mask_dir, transform)
test_size = int(0.20 * len(dataset))
train_size = len(dataset) - test_size

train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
