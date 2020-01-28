import cv2
import os
import numpy as np

from wbsrgb.wbsrg import WB
from n2n.denoiser import DeNoiser
from neurenh.enhance import NeuralEnhancer
from skimage import exposure, util
from esrgan.main import Esrgan

in_dir = './_input/'
out_dir = "./_output/"  # output directory

# wb_model = WB()
# wb = wb_model.run  # função!!

# denoiser = DeNoiser()
# denoise = denoiser.run

# enhancer = NeuralEnhancer()
# enhance = enhancer.process

grower = Esrgan()
grow = grower.run


def antiblur(image):
    # compute the Laplacian of the image and then return the focus
    # measure, which is simply the variance of the Laplacian
    blurLevel = cv2.Laplacian(image, cv2.CV_64F).var()
    print(blurLevel)
    if blurLevel < 100:
        print('blurred! correcting....')
        acr = 0
        r = (blurLevel + acr) / (100 + acr)
        r = r < 0.45 and 0.45
        h, w, c = image.shape
        dim = (int(w*r), int(h*r))
        image = cv2.resize(image, dim)
    return image


def gamma(img):
    img_sk = util.img_as_float(img)
    p2, p98 = np.percentile(img_sk, (2, 98))
    res = exposure.rescale_intensity(img_sk, in_range=(p2, p98))
    return util.img_as_ubyte(res)


def gamma2(img):
    img_sk = util.img_as_float(img)
    res = exposure.equalize_adapthist(img_sk, clip_limit=0.03)
    return util.img_as_ubyte(res)


def gamma3(img):
    img_sk = util.img_as_float(img)
    res = exposure.equalize_hist(img_sk)
    return util.img_as_ubyte(res)


def process_batch(imgs):
    # workflow 1 begins here for each image:
    print('Iniciando procesamento...')
    out1 = [wb(img) for img in imgs]
    print('Aplicada correção de cor...')
    out2 = [gamma(img) for img in out1]
    print('Aplicado ajuste de contraste (e cor) ...')
    out3 = [denoise(img) for img in out2]
    print('Fim do processamento! salvando...')

    return out3


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
    # out1 = wb(img)
    # out2 = gamma(out1)
    # out3 = denoise(out2)

    out3 = antiblur(img)
    out4 = grow(out3)

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