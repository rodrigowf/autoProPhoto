import cv2
import os

from wbsrgb.wb import WB
from iagcwd.iagcwd import run as gamma


in_dir = './_input/'
out_dir = "./_output/"  # output directory

wb_model = WB()
wb = wb_model.run  # função!!


def process_image(img):
    # workflow 1 begins here for each image:
    out1 = wb(img)
    out2 = gamma(out1)
    out3 = wb(out2)

    outImg = out3

    return outImg


def run_single():
    filename = "dogy.jpg"  # input image filename

    in_path = in_dir + '/' + filename
    img = cv2.imread(in_path)  # read the image

    outImg = process_image(img)
    cv2.imwrite(out_dir + '/' + filename, outImg)  # save it


def run_multiple():
    imgfiles = []
    valid_images = (".jpg", ".jpeg", ".png")

    for f in os.listdir(in_dir):
        if f.lower().endswith(valid_images):
            imgfiles.append(os.path.join(in_dir, f))
    for in_img in imgfiles:
        print("processing image: " + in_img + "\n")
        filename, file_extension = os.path.splitext(in_img)  # get file parts
        img = cv2.imread(in_img)  # read the image
        outImg = process_image(img)
        cv2.imwrite(out_dir + '/' + os.path.basename(filename)
                    + file_extension, outImg)  # save it

run_multiple()