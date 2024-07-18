import cv2
import numpy as np
import os
import time
import subprocess

# 获取当前脚本文件的目录
project_dir = os.path.dirname(os.path.abspath(__file__))
screenshot_dir = os.path.join(project_dir, '..', 'screenshots')
os.makedirs(screenshot_dir, exist_ok=True)

label_convert = {
    '人': 'person',
    '自行车': 'bicycle',
    '汽车': 'car',
    '摩托车': 'motorbike',
    '飞机': 'aeroplane',
    '公交车': 'bus',
    '火车': 'train',
    '卡车': 'truck',
    '船': 'boat',
    '红绿灯': 'traffic light',
    '消防栓': 'fire hydrant',
    '停车标志': 'stop sign',
    '停车计时器': 'parking meter',
    '长凳': 'bench',
    '鸟': 'bird',
    '猫': 'cat',
    '狗': 'dog',
    '马': 'horse',
    '羊': 'sheep',
    '牛': 'cow',
    '大象': 'elephant',
    '熊': 'bear',
    '斑马': 'zebra',
    '长颈鹿': 'giraffe',
    '背包': 'backpack',
    '雨伞': 'umbrella',
    '手袋': 'handbag',
    '领带': 'tie',
    '手提箱': 'suitcase',
    '飞盘': 'frisbee',
    '滑雪板': 'skis',
    '滑雪': 'snowboard',
    '运动球': 'sports ball',
    '风筝': 'kite',
    '棒球棒': 'baseball bat',
    '棒球手套': 'baseball glove',
    '滑板': 'skateboard',
    '冲浪板': 'surfboard',
    '网球拍': 'tennis racket',
    '瓶子': 'bottle',
    '酒杯': 'wine glass',
    '杯子': 'cup',
    '叉子': 'fork',
    '刀': 'knife',
    '勺子': 'spoon',
    '碗': 'bowl',
    '香蕉': 'banana',
    '苹果': 'apple',
    '三明治': 'sandwich',
    '橙子': 'orange',
    '西兰花': 'broccoli',
    '胡萝卜': 'carrot',
    '热狗': 'hot dog',
    '披萨': 'pizza',
    '甜甜圈': 'donut',
    '蛋糕': 'cake',
    '椅子': 'chair',
    '沙发': 'sofa',
    '盆栽': 'pottedplant',
    '床': 'bed',
    '餐桌': 'diningtable',
    '马桶': 'toilet',
    '电视': 'tvmonitor',
    '电脑': 'laptop',
    '鼠标': 'mouse',
    '遥控器': 'remote',
    '键盘': 'keyboard',
    '手机': 'cell phone',
    '微波炉': 'microwave',
    '烤箱': 'oven',
    '烤面包机': 'toaster',
    '水槽': 'sink',
    '冰箱': 'refrigerator',
    '书': 'book',
    '时钟': 'clock',
    '花瓶': 'vase',
    '剪刀': 'scissors',
    '泰迪熊': 'teddy bear',
    '吹风机': 'hair drier',
    '牙刷': 'toothbrush'
}


def yolo_detect(decect_lable:str, timeout=30, frame_rate=1, detect_count=10):
    print("Starting YOLO detection...")
    weight_path = os.path.join(project_dir, '..', 'nn', 'darknet', 'yolov3.weights')
    cfg_path = os.path.join(project_dir, '..', 'nn', 'darknet', 'cfg', 'yolov3.cfg')
    coco_names_path = os.path.join(project_dir, '..', 'nn', 'darknet', 'data', 'coco.names')
    # 加载 YOLO
    net = cv2.dnn.readNet(weight_path, cfg_path)
    layer_names = net.getLayerNames()
    # print("Layer Names: ", layer_names)  # 调试信息
    output_layers_indexes = net.getUnconnectedOutLayers()
    print("Output Layers Indexes: ", output_layers_indexes)  # 调试信息

    # 根据 OpenCV 版本处理 output_layers
    if isinstance(output_layers_indexes, np.ndarray) and output_layers_indexes.ndim == 1:
        output_layers = [layer_names[i - 1] for i in output_layers_indexes]
    else:
        output_layers = [layer_names[i[0] - 1] for i in output_layers_indexes]

    classes = []
    with open(coco_names_path, "r") as f:
        classes = [line.strip() for line in f.readlines()]

    # 打开视频
    vidio_url = "http://localhost:8093"
    cap = cv2.VideoCapture(vidio_url)

    # 开始计时
    start_time = time.time()
    frame_count = 0
    detected = 0
    processed_frame_count = 0
    result = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("无法读取视频帧，可能是流的问题。")
            break

        # 检查是否已超过 10 秒
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout or detected >= detect_count:
            print(f"已超过 {timeout} 秒或检测到 {detect_count} 个物体，结束检测。")
            break

        frame_count += 1

        # 只处理每 frame_rate 帧中的一帧
        if frame_count % frame_rate != 0:
            continue
        print(f"处理第 {frame_count} 帧, 已跳过其他帧")

        processed_frame_count += 1

        # 预处理图像
        height, width, channels = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        # 分析检测结果
        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:  # 只考虑置信度 > 50% 的检测结果
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # 非最大值抑制
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        output_dir = os.path.join(screenshot_dir, str(int(start_time)))
        os.makedirs(output_dir, exist_ok=True)
        # 绘制检测框
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                if label == label_convert[decect_lable]:  # 只显示检测到的物体
                    print(f"\033[32m检测到目标物体：{label_convert[decect_lable]}\033[0m")
                    detected += 1
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    # 保存截图
                    screenshot_filename = os.path.join(output_dir, f"detected_{frame_count}_{label}.png")
                    cv2.imwrite(screenshot_filename, frame)
                    result.append(f"{str(int(start_time))}/detected_{frame_count}_{label}.png")
                else:
                    print("检测到其他物体：" + label)
        # 显示结果
        # cv2.imshow("Video", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    cap.release()
    cv2.destroyAllWindows()
    print("YOLO detection completed.")
    return result


if __name__ == '__main__':
    yolo_detect()
