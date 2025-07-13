from django.shortcuts import render

# Create your views here.
# OralCancerDetectionBackend/detector_api/views.py

import os
import numpy as np
from PIL import Image
import base64
from io import BytesIO
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.inception_v3 import preprocess_input
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # Crucial for API POST requests
import json # Import the json module to parse request.body data

# OralCancerDetectionBackend/detector_api/views.py
# ... existing imports ...
from django.contrib.auth.models import User # For creating new users
from django.contrib.auth import authenticate, login # For login (will use later)
from django.views.decorators.http import require_POST # To ensure only POST requests
# ... rest of your imports
# Define the path to your model relative to the app directory.
# os.path.dirname(os.path.abspath(__file__)) gets the absolute directory of the current views.py file.
# This ensures the path is resolved correctly regardless of the current working directory when the server starts.
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model', 'oral_cancer_model.h5')
print(f"DEBUG: Attempting to load model from: {MODEL_PATH}") 

model = None
try:
    model = load_model(MODEL_PATH)
    print(f"Django: Model loaded successfully from: {MODEL_PATH}")
except Exception as e:
    print(f"Django: Error loading model: {e}")
    # Optionally, you might want to raise an exception or exit if the model is critical
    # For development, just printing the error is fine.

@csrf_exempt # Use this decorator to bypass Django's CSRF protection for this specific API endpoint.
             # This is necessary for external clients (like your JS frontend) to make POST requests.
def predict_image(request):
    # Ensure the request method is POST
    if request.method == 'POST':
        # Check if the model was loaded successfully
        if model is None:
            return JsonResponse({'error': 'Prediction service is not available (model not loaded)'}, status=500)

        try:
            # Parse the JSON body of the request. The frontend sends the image as a JSON object.
            data = json.loads(request.body)
            image_data = data.get('image') # Get the base64 image string from the 'image' key

            if not image_data:
                return JsonResponse({'error': 'No image data provided in the request payload'}, status=400)

            # Decode the base64 image string into an image object.
            # The base64 string usually starts with a prefix like "data:image/png;base64,"
            # We need to split that prefix off before decoding.
            header, encoded = image_data.split(",", 1)
            image = Image.open(BytesIO(base64.b64decode(encoded)))

            # Preprocess the image to match the input requirements of your InceptionV3 model.
            image = image.resize((299, 299)) # InceptionV3 expects 299x299 input # InceptionV3 expects 224x224 input
            image_array = np.array(image)

            # Ensure the image has 3 channels (RGB). Handle grayscale or RGBA images.
            if image_array.ndim == 2: # If it's a grayscale image (2 dimensions: height, width)
                image_array = np.stack((image_array,) * 3, axis=-1) # Convert to 3 channels by stacking
            elif image_array.shape[2] == 4: # If it's an RGBA image (4 channels)
                image_array = image_array[:, :, :3] # Keep only the RGB channels

            image_array = np.expand_dims(image_array, axis=0) # Add a batch dimension (1, height, width, channels)
            image_array = preprocess_input(image_array) # Apply InceptionV3's specific preprocessing (scaling, etc.)

            # Make the prediction
            predictions = model.predict(image_array)

            # Assuming a binary classification output (e.g., [probability_normal, probability_oral_cancer])
            # IMPORTANT: Ensure 'Normal' corresponds to index 0 and 'Oral Cancer' to index 1
            # or adjust this list to match your model's output order.
            # class_labels = ['Oral Cancer', 'Normal'] # <--- SWAP THESE LABELS
            class_labels = ['Oral Cancer', 'Normal'] # <--- CONFIRM THIS EXACT ORDER # <--- ENSURE THIS EXACT ORDER AND WORDING
            predicted_class_index = np.argmax(predictions[0]) # Get the index of the highest probability
            predicted_class = class_labels[predicted_class_index]
            confidence = float(predictions[0][predicted_class_index]) # Get the confidence score for the predicted class

            # Return the prediction result as a JSON response
            return JsonResponse({
                'prediction': predicted_class,
                'confidence': confidence
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)
        except Exception as e:
            # Catch any other unexpected errors during processing or prediction
            print(f"Prediction error: {e}")
            return JsonResponse({'error': f'An unexpected error occurred during prediction: {str(e)}'}, status=500)
    else:
        # If the request method is not POST, return a Method Not Allowed response
        return JsonResponse({'error': 'Only POST requests are allowed for this API endpoint'}, status=405)


# OralCancerDetectionBackend/detector_api/views.py

# ... (your existing code, including predict_image function) ...

@csrf_exempt
@require_POST # Ensures only POST requests are accepted for signup
def signup(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '') # Email is optional

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already taken'}, status=409) # 409 Conflict

        # Create the new user
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save() # Save the user to the database

        # You might want to automatically log in the user after signup
        # For now, we'll just return a success message.
        # user = authenticate(request, username=username, password=password)
        # if user is not None:
        #     login(request, user)

        return JsonResponse({'message': 'User registered successfully'}, status=201) # 201 Created

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        print(f"Signup error: {e}")
        return JsonResponse({'error': f'An unexpected error occurred during signup: {str(e)}'}, status=500)


# OralCancerDetectionBackend/detector_api/views.py

# ... (your existing code, including predict_image and signup functions) ...

@csrf_exempt
@require_POST # Ensures only POST requests are accepted for login
def login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If authentication is successful, log the user in
            login(request, user)
            return JsonResponse({'message': 'Logged in successfully'}, status=200)
        else:
            # If authentication fails
            return JsonResponse({'error': 'Invalid credentials'}, status=401) # 401 Unauthorized

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        print(f"Login error: {e}")
        return JsonResponse({'error': f'An unexpected error occurred during login: {str(e)}'}, status=500)