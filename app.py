from flask import Flask, request, send_file, send_from_directory
from flask_cors import CORS
from PIL import Image
import numpy as np
import cv2
import ezdxf
import io
import os

app = Flask(__name__)
CORS(app)  # Enable CORS

# Get port from environment variable or use 5000 as default
port = int(os.environ.get('PORT', 5000))

def remove_white_background(image):
    # Convert image to RGBA if it isn't already
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get the image data as a numpy array
    data = np.array(image)
    
    # Create alpha channel mask based on pixel brightness
    r, g, b, a = data.T
    
    # More aggressive white detection (lower threshold to catch more white/light pixels)
    # Adjust the threshold (200) to be more or less aggressive
    white_areas = (r > 1) & (g > 1) & (b > 1)
    
    # Force white pixels to be completely transparent
    data[..., 3] = np.where(white_areas.T, 0, 255)
    
    # Optional: Force non-white pixels to be completely black
    black_areas = ~white_areas
    data[..., 0][black_areas.T] = 0  # R
    data[..., 1][black_areas.T] = 0  # G
    data[..., 2][black_areas.T] = 0  # B
    
    return Image.fromarray(data)

def image_to_dxf(image):
    # Convert PIL image to OpenCV format
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)
    
    # Get alpha channel (0 = transparent, 255 = opaque)
    alpha = cv_image[:, :, 3]
    
    # Create binary mask from alpha channel
    _, thresh = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)
    
    # Find only external contours
    contours, hierarchy = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,  # Changed back to EXTERNAL to only get outer contours
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Create new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add only external contours to DXF
    for contour in contours:
        # Convert contour points to 2D points
        points = [(point[0][0], point[0][1]) for point in contour]
        if len(points) > 2:
            # Create closed polyline for external contour
            msp.add_lwpolyline(points, close=True)
    
    return doc

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/script.js')
def serve_script():
    return send_from_directory('static', 'script.js')

@app.route('/convert', methods=['POST'])
def convert():
    if 'image' not in request.files:
        return 'No image uploaded', 400
    
    file = request.files['image']
    
    try:
        # Read the image
        img = Image.open(file.stream)
        
        # Remove white background
        img_transparent = remove_white_background(img)
        
        # Convert to DXF
        dxf_doc = image_to_dxf(img_transparent)
        
        # Save DXF to memory
        output = io.StringIO()
        dxf_doc.write(output)
        
        # Convert to bytes for sending
        output_bytes = output.getvalue().encode('utf-8')
        output_buffer = io.BytesIO(output_bytes)
        output_buffer.seek(0)
        
        return send_file(
            output_buffer,
            mimetype='application/dxf',
            as_attachment=True,
            download_name='converted.dxf'
        )
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return 'Error processing image', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port) 