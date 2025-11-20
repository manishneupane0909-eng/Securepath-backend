from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import lightgbm as lgb


@api_view(['GET'])
def index(request):
    """API Overview"""
    return Response({
        'message': 'Welcome to Fraud Detection API',
        'version': '1.0',
        'status': 'active',
        'endpoints': {
            'GET /api/': 'API Overview',
            'GET /api/status/': 'Check API Status',
            'POST /api/upload/': 'Upload CSV',
            'POST /api/train-model/': 'Train Fraud Detection Model',
        }
    })


@api_view(['GET'])
def status_check(request):
    """Check API status"""
    return Response({
        'status': 'success',
        'message': 'Fraud Detection API is running',
        'version': '1.0'
    })


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_csv_view(request):
    """Upload CSV file"""
    print("=" * 50)
    print("REQUEST RECEIVED")
    print("METHOD:", request.method)
    print("Content-Type:", request.META.get('CONTENT_TYPE'))
    print("Available file keys:", list(request.FILES.keys()))
    print("FILES:", request.FILES)
    print("=" * 50)

    try:
        # Check if file exists in request
        if not request.FILES:
            return Response(
                {
                    'error': 'No file uploaded',
                    'details': 'Please upload a file using multipart/form-data with field name "file"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'file' not in request.FILES:
            available_keys = list(request.FILES.keys())
            return Response(
                {
                    'error': 'No file with key "file" found',
                    'details': f'Available keys: {available_keys}. Please use field name "file"',
                    'hint': 'In Insomnia: Use Multipart Form, field name must be "file", type must be File'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        csv_file = request.FILES['file']
        print(f"✓ File received: {csv_file.name}, Size: {csv_file.size} bytes")

        # Validate file type
        if not csv_file.name.endswith('.csv'):
            return Response(
                {
                    'error': 'Invalid file type',
                    'details': f'File "{csv_file.name}" is not a CSV file. Please upload a .csv file'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read CSV
        print("Reading CSV...")
        df = pd.read_csv(csv_file)
        print(f"✓ CSV read successfully: {len(df)} rows, {len(df.columns)} columns")

        return Response({
            'status': 'success',
            'message': 'CSV uploaded successfully',
            'file_info': {
                'filename': csv_file.name,
                'size': csv_file.size,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'data_types': df.dtypes.astype(str).to_dict(),
                'missing_values': df.isnull().sum().to_dict(),
                'sample_data': df.head(3).to_dict('records')
            }
        }, status=status.HTTP_200_OK)

    except pd.errors.EmptyDataError:
        print("✗ ERROR: CSV file is empty")
        return Response(
            {'error': 'CSV file is empty'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except pd.errors.ParserError as e:
        print(f"✗ ERROR: CSV parsing error: {str(e)}")
        return Response(
            {'error': f'Invalid CSV format: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"✗ EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error processing file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def train_model(request):
    """Upload CSV and train fraud detection model"""
    print("=" * 50)
    print("TRAIN MODEL REQUEST RECEIVED")
    print("Content-Type:", request.META.get('CONTENT_TYPE'))
    print("Available file keys:", list(request.FILES.keys()))
    print("=" * 50)

    try:
        # Check if file exists
        if not request.FILES:
            return Response(
                {
                    'error': 'No file uploaded',
                    'details': 'Please upload a CSV file using multipart/form-data with field name "file"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'file' not in request.FILES:
            available_keys = list(request.FILES.keys())
            return Response(
                {
                    'error': 'No file with key "file" found',
                    'details': f'Available keys: {available_keys}. Please use field name "file"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        csv_file = request.FILES['file']
        print(f"✓ Training with file: {csv_file.name}")

        # Validate file type
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': f'Invalid file type. Expected .csv, got {csv_file.name}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read CSV
        df = pd.read_csv(csv_file)
        print(f"✓ Data loaded: {len(df)} rows, {len(df.columns)} columns")

        # Basic data validation
        if len(df) == 0:
            return Response(
                {'error': 'CSV file is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        info = {
            'status': 'success',
            'message': 'CSV file uploaded successfully',
            'data_info': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': list(df.columns),
                'data_types': df.dtypes.astype(str).to_dict(),
                'missing_values': df.isnull().sum().to_dict(),
                'sample_data': df.head(5).to_dict('records')
            }
        }

        return Response(info, status=status.HTTP_200_OK)

    except pd.errors.EmptyDataError:
        print("✗ ERROR: CSV file is empty")
        return Response(
            {'error': 'CSV file is empty'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except pd.errors.ParserError as e:
        print(f"✗ ERROR: CSV parsing error: {str(e)}")
        return Response(
            {'error': f'Invalid CSV format: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"✗ EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error processing file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )