from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import base64
import io
from database import init_database, add_submission, get_random_submission, get_submission_count

# Create Flask app
app = Flask(__name__)
CORS(app)  # Allows frontend to communicate with backend

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_canvas_drawing(canvas_data):
    """Process and save canvas drawing from base64 data"""
    try:
        # Remove data URL prefix (data:image/png;base64,)
        if canvas_data.startswith('data:image'):
            canvas_data = canvas_data.split(',')[1]
        
        # Decode base64 to image
        image_data = base64.b64decode(canvas_data)
        image = Image.open(io.BytesIO(image_data))
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Resize if too large (keep aspect ratio)
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(file_path, 'PNG')
        
        return unique_filename
    except Exception as e:
        print(f"Error processing canvas drawing: {e}")
        return None

def process_uploaded_file(file):
    """Process and save uploaded image file"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Open and resize image to reasonable size
    try:
        image = Image.open(file)
        # Resize if too large (keep aspect ratio)
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(file_path)
        return unique_filename
    except Exception as e:
        print(f"Error processing uploaded image: {e}")
        return None

# Routes (URL endpoints)

@app.route('/')
def home():
    """Homepage - redirect to input interface"""
    return render_template('input.html')

@app.route('/input')
def input_page():
    """Input interface where users submit content"""
    return render_template('input.html')

@app.route('/orb')
def orb_page():
    """Orb interface where users scry for content"""
    total_submissions = get_submission_count()
    return render_template('orb.html', total_submissions=total_submissions)

@app.route('/api/submit', methods=['POST'])
def submit_content():
    """API endpoint to handle content submissions"""
    try:
        # Get text content
        text_content = request.form.get('text_content', '').strip()
        
        # Check for canvas drawing data
        canvas_data = request.form.get('canvas_data')
        doodle_filename = None
        
        if canvas_data and canvas_data != 'null':
            # Process canvas drawing
            doodle_filename = process_canvas_drawing(canvas_data)
        else:
            # Check for uploaded file
            uploaded_file = request.files.get('doodle_file')
            if uploaded_file:
                doodle_filename = process_uploaded_file(uploaded_file)
        
        # Must have either text or doodle
        if not text_content and not doodle_filename:
            return jsonify({'error': 'Must provide either text or doodle'}), 400
        
        # Save to database
        submission_id = add_submission(
            text_content=text_content if text_content else None,
            doodle_filename=doodle_filename
        )
        
        if submission_id:
            return jsonify({
                'success': True,
                'message': 'Your essence has been captured by the orb...',
                'submission_id': submission_id
            })
        else:
            return jsonify({'error': 'Failed to save submission'}), 500
            
    except Exception as e:
        print(f"Error in submit_content: {e}")
        return jsonify({'error': 'Something went wrong'}), 500

@app.route('/api/scry', methods=['GET'])
def scry_orb():
    """API endpoint to get random submission from orb"""
    try:
        submission = get_random_submission()
        
        if submission:
            return jsonify({
                'success': True,
                'submission': submission
            })
        else:
            return jsonify({
                'success': False,
                'message': 'The orb is empty... no visions to see'
            })
            
    except Exception as e:
        print(f"Error in scry_orb: {e}")
        return jsonify({'error': 'The orb refuses to reveal its secrets'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint to get orb statistics"""
    try:
        count = get_submission_count()
        return jsonify({
            'total_submissions': count
        })
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': 'Cannot read orb statistics'}), 500

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded doodle images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    print("🔮 Mystical Orb server starting...")
    print("📝 Input interface: http://localhost:5000/input")
    print("🌟 Orb interface: http://localhost:5000/orb")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)