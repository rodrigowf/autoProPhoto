import os
import cv2
import numpy as np

from skimage import exposure, util
from wbsrgb.wbsrg import WB
from n2n.denoiser import DeNoiser
from neurenh.enhance import NeuralEnhancer
from esrgan.main import Esrgan


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


def antiblur(image):
    # compute the Laplacian of the image and then return the focus
    # measure, which is simply the variance of the Laplacian
    blurLevel = cv2.Laplacian(image, cv2.CV_64F).var()
    print(blurLevel)
    if blurLevel < 100:
        print('blurred! correcting....')
        acr = 30
        # if blurLevel < 30:
        #     acr = 40
        # elif blurLevel < 50:
        #     acr = 20
        r = (blurLevel + acr) / (100 + acr)
        h, w, c = image.shape
        dim = (int(w*r), int(h*r))
        image = cv2.resize(image, dim)
    return image


def grow(image):
    h, w, c = image.shape
    higher_dim = max(h, w)
    if higher_dim < 750:
        result = grower4.run(image)
    elif higher_dim < 1300:
        result = grower2.process(image)
    else:
        result = image
    return result


# ----------------------------------------------------


def process_batch(imgs):
    # workflow 1 begins here for each batch:

    print('Iniciando procesamento ...')
    wb = WB()
    out1 = [wb.run(img) for img in imgs]
    del wb

    print('Aplicada correção de cor ...')
    out2 = [gamma(img) for img in out1]
    del out1

    print('Removendo ruido ...')
    denoiser = DeNoiser()
    out3 = [denoiser.run(img) for img in out2]
    del denoiser
    del out2

    print('Removendo blur ...')
    out4 = [antiblur(img) for img in out3]
    del out3

    print('Aplicado ampliação ...')
    global grower2
    global grower4
    grower2 = NeuralEnhancer()
    grower4 = Esrgan()
    out5 = [grow(img) for img in out4]
    del grower2
    del grower4
    del out4

    print('Fim do processamento! salvando ...')
    return out5


def run_batch(input_dir, output_dir):
    imgs = []
    names = []
    valid_images = (".jpg", ".jpeg", ".png")

    for f in os.listdir(input_dir):  # ve tudo o que tem na pasta dada...
        if f.lower().endswith(valid_images):  # se for um dos arquivos válidos:
            filepath = os.path.join(input_dir, f)
            filename, file_extension = os.path.splitext(filepath)  # get file parts
            img = cv2.imread(filepath)  # read the image
            imgs.append(img)
            names.append(os.path.basename(filename)+file_extension)

    results = process_batch(imgs)  # aqui q toda a mágica acontece! ;)

    i = 0
    for img in results:
        cv2.imwrite(output_dir + '/' + names[i], img)  # save it
        i = i+1

    print('tudo salvo! vá na paz!!')


def load_all_libs():
    global wb
    global denoiser
    global grower2
    global grower4

    wb = WB()
    denoiser = DeNoiser()
    grower2 = NeuralEnhancer()
    grower4 = Esrgan()


def clean_all_libs():
    del wb
    del denoiser
    del grower2
    del grower4


def process_image(img):
    # workflow 1 begins here for each image:
    print('white balance ........')
    out1 = wb.run(img)
    print('gamma ........')
    out2 = gamma(out1)
    print('denoising ........')
    out3 = denoiser.run(out2)
    print('antiblur ........')
    out4 = antiblur(out3)
    print('crescendo ........')
    out5 = grow(out4)
    print('feito!')
    return out5


def run_single(in_path, out_dir):
    load_all_libs()

    filename = os.path.basename(in_path)

    img = cv2.imread(in_path)  # read the image
    outImg = process_image(img)
    cv2.imwrite(out_dir + '/' + filename, outImg)  # save it


def run_multiple(input_dir, output_dir):
    load_all_libs()

    imgfiles = []
    valid_images = (".jpg", ".jpeg", ".png")

    for f in os.listdir(input_dir):
        if f.lower().endswith(valid_images):
            imgfiles.append(os.path.join(input_dir, f))
    for in_img in imgfiles:
        print("processing image: " + in_img + "\n")
        filename, file_extension = os.path.splitext(in_img)  # get file parts
        img = cv2.imread(in_img)  # read the image
        outImg = process_image(img)
        cv2.imwrite(output_dir + '/' + os.path.basename(filename)
                    + file_extension, outImg)  # save it



# in_dir = './_input/'
# out_dir = "./_output/"  # output directory
# run_multiple(in_dir, out_dir)