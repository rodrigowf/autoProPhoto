import scipy
import numpy as np
import cv2

def get_imgs_fn(file_name):
	return cv2.imread(file_name)

def augment_imgs_fn(x, add_noise=True):
	return x+0.1*x.std()*np.random.random(x.shape)

def normalize_imgs_fn(x):
    # x = x * (2./ 255.) - 1.
    # x = x * (1./255.)
    return x

def truncate_imgs_fn(x):
	x = np.where(x > -1., x, -1.)
	x = np.where(x < 1., x, 1.)
	return x