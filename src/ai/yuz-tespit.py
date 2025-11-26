from mtcnn import MTCNN
from mtcnn.utils.plotting import plot
from PIL import Image
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import matplotlib.pyplot as plt
import numpy as np

def load_image_via_dialog():
    root = Tk()
    root.withdraw()

    file_path = askopenfilename(
        title="Bir resim seçin",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp")],
    )

    if not file_path:
        print("Hiçbir dosya seçilmedi.")
        return None

    # RGB modunda aç ve NumPy array'e çevir (uint8)
    return np.array(Image.open(file_path).convert("RGB"), dtype=np.uint8)

image = load_image_via_dialog()
if image is None:
    exit()

# CPU kullanımı Windows için güvenli
mtcnn = MTCNN(device="CPU:0")

result = mtcnn.detect_faces(image, threshold_onet=0.85)

plt.imshow(plot(image, result))
plt.axis("off")
plt.show()
