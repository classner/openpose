import numpy as np
import cv2
import sys


class Controller:
    def __init__(self, img_path):
        self.quit = False
        self.img_path = img_path
        self.scale = 3

        self.parts = [
            'Right ankle',
            'Right knee',
            'Right hip',
            'Left hip',
            'Left knee',
            'Left ankle',
            'Right wrist',
            'Right elbow',
            'Right shoulder',
            'Left shoulder',
            'Left elbow',
            'Left wrist',
            'Neck',
            'Head top',
            ]

        self.coordinates = np.zeros((2, len(self.parts)))
        self.visible = np.zeros((len(self.parts)))

        self.current_part = 0
        print(self.parts[self.current_part])

    def onmouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_RBUTTONDOWN:
            self.coordinates[:, self.current_part] = (
                np.array([x, y]) / float(self.img.shape[0]))

            self.visible[self.current_part] = (event == cv2.EVENT_LBUTTONDOWN)

            self.current_part += 1

            if self.current_part == len(self.parts):
                self.quit = True
            else:
                print(self.parts[self.current_part])

    def go(self):
        cv2.namedWindow('img')
        cv2.setMouseCallback('img', lambda *args: self.onmouse(*args))

        original_img = cv2.imread(self.img_path)
        self.img = cv2.resize(
            original_img,
            (original_img.shape[1] * self.scale, original_img.shape[0] *
             self.scale),
            interpolation=cv2.INTER_NEAREST)

        self.img_rectangle = self.img.copy()

        while not self.quit:
            cv2.imshow('img', self.img_rectangle)

            # get a key
            k = 0xFF & cv2.waitKey(1)

            # esc
            if k == 27:
                break

        cv2.destroyAllWindows()

        print('new_parts = {}'.format(self.coordinates.transpose().tolist()))
        print('new_visible = {}'.format(self.visible.tolist()))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <image>")
        exit(1)

    c = Controller(sys.argv[1])
    c.go()
