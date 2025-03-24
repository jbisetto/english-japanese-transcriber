import boto3
import json
from typing import Dict, Any

class BedrockClient:
    def __init__(self, region: str = None):
        """
        Initializes the Bedrock client.

        Args:
            region (str, optional): The AWS region to use. Defaults to None,
                                     which uses the default region configured
                                     in the environment.
        """
        self.bedrock = boto3.client("bedrock-runtime", region_name=region)

    def invoke_model(self, model_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes a Bedrock model.

        Args:
            model_id (str): The ID of the Bedrock model to invoke.
            body (Dict[str, Any]): The request body for the model.

        Returns:
            Dict[str, Any]: The response from the model.
        """
        try:
            response = self.bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            return json.loads(response["body"].read().decode("utf-8"))
        except Exception as e:
            print(f"Error invoking model: {e}")
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
