import numpy as np
from .model import get_model


class DeNoiser:

    def __init__(self):
        # weight_file = 'n2n/weights.040-87.447-29.13496_gauss_noise.hdf5'  # esse aqui mostrou results melhores
        weight_file = 'n2n/weights.056-66.803-30.57923_gauss_clean.hdf5'  # trained weight file
        self.model = get_model("srresnet")  # model architecture ('srresnet' or 'unet')
        self.model.load_weights(weight_file)

    def get_image(self, image):
        image = np.clip(image, 0, 255)
        return image.astype(dtype=np.uint8)

    def run(self, image):
        h, w, _ = image.shape
        image = image[:(h // 16) * 16, :(w // 16) * 16]  # for stride (maximum 16)
        h, w, _ = image.shape

        noise_image = image
        pred = self.model.predict(np.expand_dims(noise_image, 0))
        denoised_image = self.get_image(pred[0])

        return denoised_image
