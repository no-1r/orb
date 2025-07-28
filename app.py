from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import base64
import io
from database import init_database, add_submission, get_random_submission, get_submission_count


app = Flask(__name__)
CORS(app)  


app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def validate_image_file(file):
    """Security File Validation"""
    if not file or not file.filename:
        return False, "No file provided"
    
   
    if not allowed_file(file.filename):
        return False, "Invalid file type. Only PNG, JPG, and GIF allowed"
    
   
    file_content = file.read()
    file.seek(0)  
    
   
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            img.verify()  
        
        file.seek(0)  
        with Image.open(file) as img:
            if img.format.lower() not in ['png', 'jpeg', 'gif']:
                return False, "File format not supported"
            
    except Exception:
        return False, "File is not a valid image"
    
    
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        return False, "File too large. Maximum size is 5MB"
    
    file.seek(0)  
    return True, "Valid image"

def sanitize_and_process_image(file):
    """Sanitize and process uploaded image"""
    try:
        
        image = Image.open(file)
        
        
        if image.mode not in ('RGB', 'L'):  
            image = image.convert('RGB')
        
       
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
       
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        
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
        
        if not canvas_data or not canvas_data.startswith('data:image'):
            return None, "Invalid canvas data"
        
       
        canvas_data = canvas_data.split(',')[1]
        
      
        try:
            image_data = base64.b64decode(canvas_data)
        except Exception:
            return None, "Invalid base64 data"
        
        
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                img.verify()  
                
            
            image = Image.open(io.BytesIO(image_data))
        except Exception:
            return None, "Canvas data is not a valid image"
        
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
       
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        
        image.save(file_path, 'PNG', optimize=True)
        
        return unique_filename, None
        
    except Exception as e:
        return None, f"Error processing canvas: {str(e)}"

def process_uploaded_file(file):
    """Process and save uploaded image file"""
    if not file or not allowed_file(file.filename):
        return None
    
    
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    
    try:
        image = Image.open(file)
       
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(file_path)
        return unique_filename
    except Exception as e:
        print(f"Error processing uploaded image: {e}")
        return None



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
        
        text_content = request.form.get('text_content', '').strip()
        
        
        canvas_data = request.form.get('canvas_data')
        uploaded_file = request.files.get('doodle_file')
        
        doodle_filename = None
        error_message = None
        
        
        if canvas_data and canvas_data != 'null' and uploaded_file and uploaded_file.filename:
            return jsonify({'error': 'Cannot submit both drawing and file upload. Choose one.'}), 400
        
        
        if canvas_data and canvas_data != 'null':
            doodle_filename, error_message = process_canvas_drawing(canvas_data)
            if error_message:
                return jsonify({'error': error_message}), 400
        
       
        elif uploaded_file and uploaded_file.filename:
           
            is_valid, validation_message = validate_image_file(uploaded_file)
            if not is_valid:
                return jsonify({'error': validation_message}), 400
            
            
            doodle_filename, error_message = sanitize_and_process_image(uploaded_file)
            if error_message:
                return jsonify({'error': error_message}), 400
        
        
        if not text_content and not doodle_filename:
            return jsonify({'error': 'Must provide either text or image'}), 400
        
        
        if text_content:
           
            text_content = text_content.strip()[:2000]  
            if not text_content:  
                text_content = None
        
        
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


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded doodle images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def home():
    """Homepage - redirect to orb interface"""
    return render_template('orb.html', total_submissions=get_submission_count())

if __name__ == '__main__':
    init_database()
    print("dusting off orb...")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)