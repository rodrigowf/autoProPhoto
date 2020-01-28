import numpy as np
import torch
from . import RRDBNet_arch as arch


class Esrgan:
    def __init__(self):
        model_path = 'esrgan/models/interp_08.pth'  # models/RRDB_ESRGAN_x4.pth OR models/RRDB_PSNR_x4.pth
        # self.device = torch.device('cuda')  # if you want to run on CPU, change 'cuda' -> cpu
        self.device = torch.device('cuda')

        model = arch.RRDBNet(3, 3, 64, 23, gc=32)
        model.load_state_dict(torch.load(model_path), strict=True)
        model.eval()
        self.model = model.to(self.device)

        print('Model path {:s}. \nTesting...'.format(model_path))

    def run(self, img):
        img = img * 1.0 / 255
        img = torch.from_numpy(np.transpose(img[:, :, [2, 1, 0]], (2, 0, 1))).float()
        img_LR = img.unsqueeze(0)
        img_LR = img_LR.to(self.device)

        with torch.no_grad():
            output = self.model(img_LR).data.squeeze().float().cpu().clamp_(0, 1).numpy()
        output = np.transpose(output[[2, 1, 0], :, :], (1, 2, 0))
        output = (output * 255.0).round()

        return output
