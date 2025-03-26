import pytest
from unittest.mock import Mock, patch
from src.aws.bedrock_client import BedrockClient
import json
import botocore

def test_bedrock_client_initialization():
    """Test BedrockClient initialization with different region settings"""
    # Test with specific region
    client = BedrockClient(region="us-west-2")
    assert client.bedrock.meta.region_name == "us-west-2"
    
    # Test with default region
    with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
        client = BedrockClient()
        assert client.bedrock.meta.region_name == "us-east-1"

def test_invoke_model_success():
    """Test successful model invocation with mocked response"""
    # Create unique test data for this test
    test_model_id = "test.model.123"
    test_input = {"prompt": "Test prompt", "max_tokens": 100}
    expected_response = {"generated_text": "Test response"}
    
    # Create mock response object
    mock_response = {
        "body": Mock(
            read=Mock(return_value=json.dumps(expected_response).encode('utf-8'))
        )
    }
    
    # Mock the boto3 client
    with patch('boto3.client') as mock_boto3:
        # Configure mock
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = mock_response
        mock_boto3.return_value = mock_bedrock
        
        # Create client and invoke model
        client = BedrockClient()
        response = client.invoke_model(test_model_id, test_input)
        
        # Verify response
        assert response == expected_response
        
        # Verify mock was called correctly
        mock_bedrock.invoke_model.assert_called_once_with(
            modelId=test_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(test_input)
        )

def test_invoke_model_client_error():
    """Test handling of boto3 client errors"""
    # Create unique test data
    test_model_id = "test.error.model"
    test_input = {"prompt": "Error test"}
    
    # Create mock error
    error_response = {
        'Error': {
            'Code': 'ModelNotFound',
            'Message': 'Model not found'
        }
    }
    client_error = botocore.exceptions.ClientError(error_response, 'invoke_model')
    
    # Mock boto3 client to raise error
    with patch('boto3.client') as mock_boto3:
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = client_error
        mock_boto3.return_value = mock_bedrock
        
        # Create client and test error handling
        client = BedrockClient()
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            client.invoke_model(test_model_id, test_input)
        
        assert exc_info.value.response['Error']['Code'] == 'ModelNotFound'

def test_invoke_model_throttling():
    """Test handling of throttling errors"""
    # Create unique test data
    test_model_id = "test.throttle.model"
    test_input = {"prompt": "Throttle test"}
    
    # Create throttling error
    error_response = {
        'Error': {
            'Code': 'ThrottlingException',
            'Message': 'Rate exceeded'
        }
    }
    throttling_error = botocore.exceptions.ClientError(error_response, 'invoke_model')
    
    # Mock boto3 client to raise throttling error
    with patch('boto3.client') as mock_boto3:
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = throttling_error
        mock_boto3.return_value = mock_bedrock
        
        # Create client and test error handling
        client = BedrockClient()
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            client.invoke_model(test_model_id, test_input)
        
        assert exc_info.value.response['Error']['Code'] == 'ThrottlingException' 