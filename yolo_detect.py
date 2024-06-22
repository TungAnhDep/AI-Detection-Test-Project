import os
from flask import Flask, request, redirect, url_for, render_template
import cv2
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]


classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

target_classes = ["cat", "dog"]
target_indices = [classes.index(cls) for cls in target_classes]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        image_url = detect_objects(file_path)
        return render_template('index.html', image_url=image_url)
    return redirect(request.url)

def detect_objects(image_path):
    img = cv2.imread(image_path)
    height, width, channels = img.shape

    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and class_id in target_indices:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    font = cv2.FONT_HERSHEY_PLAIN
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            color = (0, 255, 0)  

            
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)

            
            label_size, base_line = cv2.getTextSize(label, font, 1, 2)
            label_y = y + h - 10  
            if label_y - label_size[1] < y:
                label_y = y + label_size[1]  

          
            cv2.rectangle(img, (x, label_y - label_size[1]), (x + label_size[0], label_y + base_line), color, cv2.FILLED)
            
            
            cv2.putText(img, label, (x, label_y), font, 1, (0, 0, 0), 2)  

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_' + os.path.basename(image_path))
    cv2.imwrite(output_path, img)
    return url_for('static', filename='uploads/' + 'output_' + os.path.basename(image_path))


if __name__ == '__main__':
    app.run(debug=True)
