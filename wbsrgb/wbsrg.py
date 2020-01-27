## White balancing images
#
# Copyright (c) 2018-present, Mahmoud Afifi
# York University, Canada
# mafifi@eecs.yorku.ca | m.3afifi@gmail.com
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
# All rights reserved.
#
# Please cite the following work if this program is used:
# Mahmoud Afifi, Brian Price, Scott Cohen, and Michael S. Brown,
# "When color constancy goes wrong: Correcting improperly white-balanced
# images", CVPR 2019.
#
##########################################################################

import numpy as np
import cv2
import os
from .classes import WBsRGB as wb_srgb


class WB:

    def __init__(self, save_result=False, out_dir='./_output/wbsrg/'):

        # input and options
        self.upgraded_model = 1  # use 1 to load our new model that is upgraded with new training examples.
        self.gamut_mapping = 2  # use 1 for scaling, 2 for clipping (our paper's results reported
        # using clipping). If the image is over-saturated, scaling is recommended.

        self.imshow = 0  # show input/output image

        self.save_result = save_result
        self.out_dir = out_dir

        self.wbModel = wb_srgb.WBsRGB(gamut_mapping=self.gamut_mapping,
                                      upgraded=self.upgraded_model)  # create an instance of the WB model

    def ResizeWithAspectRatio(self, image, width=None, height=None, inter=cv2.INTER_AREA):
        dim = None
        (h, w) = image.shape[:2]

        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))

        return cv2.resize(image, dim, interpolation=inter)

    def run(self, img):

        # processing
        outImg = self.wbModel.correctImage(img)  # white balance it

        if self.save_result:
            os.makedirs(self.out_dir, exist_ok=True)  # verifica se a pasta de saida realmente existe
            cv2.imwrite(self.out_dir + '/' + 'result.jpg', outImg * 255)  # save it if asked

        if self.imshow == 1:
            cv2.imshow('input', self.ResizeWithAspectRatio(img, width=600))
            cv2.imshow('our result', self.ResizeWithAspectRatio(outImg, width=600))
            cv2.waitKey()
            cv2.destroyAllWindows()

        return (outImg * 255).astype(np.uint8)
