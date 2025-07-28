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
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def validate_image_file(file):
    """Validate uploaded image file for security"""
    if not file or not file.filename:
        return False, "No file provided"
    
    # Check file extension
    if not allowed_file(file.filename):
        return False, "Invalid file type. Only PNG, JPG, and GIF allowed"
    
    # Read file content to validate
    file_content = file.read()
    file.seek(0)  # Reset file pointer
    
    # Check if it's actually an image using PIL
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            # Verify it's a valid image format
            img.verify()  # This will raise an exception if not a valid image
            
        # Check format is allowed
        file.seek(0)  # Reset again after verify()
        with Image.open(file) as img:
            if img.format.lower() not in ['png', 'jpeg', 'gif']:
                return False, "File format not supported"
            
    except Exception:
        return False, "File is not a valid image"
    
    # Check file size (additional check beyond Flask's MAX_CONTENT_LENGTH)
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        return False, "File too large. Maximum size is 5MB"
    
    file.seek(0)  # Reset file pointer for later processing
    return True, "Valid image"

def sanitize_and_process_image(file):
    """Sanitize and process uploaded image"""
    try:
        # Open with PIL to strip metadata and re-encode
        image = Image.open(file)
        
        # Convert to RGB if necessary (handles RGBA, CMYK, etc.)
        if image.mode not in ('RGB', 'L'):  # L for grayscale
            image = image.convert('RGB')
        
        # Resize if too large (security and performance)
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Generate secure filename
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save as PNG (strips all metadata, consistent format)
        image.save(file_path, 'PNG', optimize=True)
        
        return unique_filename, None
        
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_canvas_drawing(canvas_data):
    """Process and save canvas drawing from base64 data"""
    try:
        # Remove data URL prefix and validate
        if not canvas_data or not canvas_data.startswith('data:image'):
            return None, "Invalid canvas data"
        
        # Extract base64 data
        canvas_data = canvas_data.split(',')[1]
        
        # Decode and validate
        try:
            image_data = base64.b64decode(canvas_data)
        except Exception:
            return None, "Invalid base64 data"
        
        # Validate it's actually an image using PIL
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                img.verify()  # Verify it's a valid image
                
            # Process with PIL for security (open again after verify)
            image = Image.open(io.BytesIO(image_data))
        except Exception:
            return None, "Canvas data is not a valid image"
        
        # Convert to RGB mode for consistency
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Resize if too large
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save securely
        image.save(file_path, 'PNG', optimize=True)
        
        return unique_filename, None
        
    except Exception as e:
        return None, f"Error processing canvas: {str(e)}"

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
        uploaded_file = request.files.get('doodle_file')
        
        doodle_filename = None
        error_message = None
        
        # Only allow ONE type of image input
        if canvas_data and canvas_data != 'null' and uploaded_file and uploaded_file.filename:
            return jsonify({'error': 'Cannot submit both drawing and file upload. Choose one.'}), 400
        
        # Process canvas drawing
        if canvas_data and canvas_data != 'null':
            doodle_filename, error_message = process_canvas_drawing(canvas_data)
            if error_message:
                return jsonify({'error': error_message}), 400
        
        # Process uploaded file
        elif uploaded_file and uploaded_file.filename:
            # Validate the uploaded file
            is_valid, validation_message = validate_image_file(uploaded_file)
            if not is_valid:
                return jsonify({'error': validation_message}), 400
            
            # Process and sanitize the file
            doodle_filename, error_message = sanitize_and_process_image(uploaded_file)
            if error_message:
                return jsonify({'error': error_message}), 400
        
        # Must have either text or image
        if not text_content and not doodle_filename:
            return jsonify({'error': 'Must provide either text or image'}), 400
        
        # Sanitize text content
        if text_content:
            # Basic text sanitization - remove excessive whitespace, limit length
            text_content = text_content.strip()[:2000]  # Limit to 2000 characters
            if not text_content:  # If only whitespace
                text_content = None
        
        # Save to database
        submission_id = add_submission(
            text_content=text_content,
            doodle_filename=doodle_filename
        )
        
        if submission_id:
            return jsonify({
                'success': True,
                'message': 'received',
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