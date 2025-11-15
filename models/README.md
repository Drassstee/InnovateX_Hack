# Models Directory

Place your trained YOLO model file here as `unified.pt`.

## Training Your Model

1. Prepare your dataset in the following structure:
   ```
   dataset/
     images/
       train/
       val/
       test/
     labels/
       train/
       val/
       test/
   ```

2. Create the training YAML:
   ```bash
   python yolo_pipeline.py --create-yaml
   ```

3. Train the model:
   ```bash
   yolo detect train data=datasets/digital_inspector.yaml model=yolov8s.pt imgsz=1024 epochs=50
   ```

4. Copy the trained model:
   ```bash
   copy runs\detect\train\weights\best.pt models\unified.pt
   ```

## Using the Model

Once you have `unified.pt` in this directory, you can run detection:

```bash
python yolo_pipeline.py your_image.jpg
```

This will create:
- `your_image_annotated.jpg` - Image with bounding boxes
- `your_image_detections.json` - Detection results in JSON format

