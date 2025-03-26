import boto3
import botocore
import json
import os
from typing import Dict, Any, Optional

class BedrockClient:
    def __init__(self, region: Optional[str] = None):
        """
        Initializes the Bedrock client.

        Args:
            region (str, optional): The AWS region to use. If None, uses the default region
                                  from AWS_DEFAULT_REGION environment variable.
        """
        self.region = region or os.environ.get('AWS_DEFAULT_REGION')
        self.bedrock = boto3.client("bedrock-runtime", region_name=self.region)

    def invoke_model(self, model_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes a Bedrock model with proper error handling.

        Args:
            model_id (str): The ID of the Bedrock model to invoke.
            body (Dict[str, Any]): The request body for the model.

        Returns:
            Dict[str, Any]: The response from the model.

        Raises:
            botocore.exceptions.ClientError: If the model invocation fails due to client errors
                including ModelNotFound, ValidationError, or ThrottlingException.
            botocore.exceptions.BotoCoreError: If there are AWS SDK-related errors.
            Exception: For any other unexpected errors.
        """
        try:
            response = self.bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            return json.loads(response["body"].read().decode("utf-8"))
            
        except botocore.exceptions.ClientError as e:
            # Handle specific AWS service errors
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # Log the error (you might want to use proper logging here)
            print(f"AWS Bedrock Error: {error_code} - {error_message}")
            
            # Re-raise the error for handling by the caller
            raise
            
        except botocore.exceptions.BotoCoreError as e:
            # Handle AWS SDK-related errors
            print(f"AWS SDK Error: {str(e)}")
            raise
            
        except Exception as e:
            # Handle any other unexpected errors
            print(f"Unexpected error during model invocation: {str(e)}")
            raise

if __name__ == '__main__':
    # Example usage (replace with your actual model ID and request body)
    bedrock_client = BedrockClient()
    model_id = "anthropic.claude-v2"  # Replace with your model ID
    body = {
        "prompt": "Write a short poem about the ocean.",
        "max_tokens_to_sample": 200,
    }
    try:
        response = bedrock_client.invoke_model(model_id, body)
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Failed to invoke model: {e}")
