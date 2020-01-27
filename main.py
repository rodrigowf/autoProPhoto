import cv2
import os

from wbsrgb.wbsrg import WB
from iagcwd.iagcwd import run as gamma
from n2n.denoiser import DeNoiser
from neurenh.enhance import NeuralEnhancer


in_dir = './_input/'
out_dir = "./_output/"  # output directory

wb_model = WB()
wb = wb_model.run  # função!!

denoiser = DeNoiser()
denoise = denoiser.run

# enhancer = NeuralEnhancer()
# enhance = enhancer.process


def process_batch(imgs):
    # workflow 1 begins here for each image:
    out1 = [wb(img) for img in imgs]

    print('aplicada correção de cor...')

    out3 = []
    for img in out1:
        out2, gm_ed = gamma(img)
        out3.append( wb(out2) if gm_ed else img )

    print('aplicado ajuste de contraste (e cor) ...')

    out4 = [denoise(img) for img in out3]

    return out4


def run_batch():
    imgs = []
    names = []
    valid_images = (".jpg", ".jpeg", ".png")

    for f in os.listdir(in_dir):  # ve tudo o que tem na pasta dada...
        if f.lower().endswith(valid_images):  # se for um dos arquivos válidos:
            filepath = os.path.join(in_dir, f)
            filename, file_extension = os.path.splitext(filepath)  # get file parts
            img = cv2.imread(filepath)  # read the image
            imgs.append(img)
            names.append(os.path.basename(filename)+file_extension)

    results = process_batch(imgs)

    i = 0
    for img in results:
        cv2.imwrite(out_dir + '/' + names[i], img)  # save it
        i = i+1


def process_image(img):

    # workflow 1 begins here for each image:
    out1 = wb(img)
    out2, gm_ed = gamma(out1)
    out3 = wb(out2) if gm_ed else out1
    out4 = enhance(out3)

    return out4


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