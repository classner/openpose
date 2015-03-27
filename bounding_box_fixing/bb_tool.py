import numpy as np
import cv2
import sys

class Controller:
    def __init__(self, img_path):
        self.mousedown = False
        self.img_path = img_path
        self.rectangle_color = [255, 0, 0]
        self.scale = 3
        self.quit = False

    def onmouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.mousedown = True
            self.start_corner = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.mousedown:
                self.img_rectangle = self.img.copy()
                cv2.rectangle(self.img_rectangle, self.start_corner, (x, y),
                        self.rectangle_color, 2)

                self.rect = np.array([
                    min(self.start_corner[0], x),
                    min(self.start_corner[1], y),
                    max(self.start_corner[0], x),
                    max(self.start_corner[1], y)]) / self.scale

        elif event == cv2.EVENT_LBUTTONUP:
            self.mousedown = False
            self.quit = True

    def go(self):
        cv2.namedWindow('img')
        cv2.setMouseCallback('img', lambda *args: self.onmouse(*args))


        original_img = cv2.imread(self.img_path)
        self.img = cv2.resize(original_img,
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

        print("{} {} {} {}".format(self.rect[0], self.rect[1], self.rect[2],
            self.rect[3]))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <image>")
        exit(1)

    c = Controller(sys.argv[1])
    c.go()
