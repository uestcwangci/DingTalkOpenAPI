from io import BytesIO

from PIL import Image


def take_screenshot_and_compress(img_path, quality=10):

    # 打开截图文件并进行压缩
    with Image.open(img_path) as img:
        # 创建一个BytesIO对象用于保存压缩后的图像数据
        compressed_io = BytesIO()

        # 将图像保存到BytesIO对象中，指定压缩质量
        img.save(compressed_io, format='PNG', optimize=True, quality=quality)

        # 将压缩后的数据写回到文件中
        with open(img_path, 'wb') as f:
            f.write(compressed_io.getvalue())

    print(f"Screenshot saved and compressed at: {img_path}")


