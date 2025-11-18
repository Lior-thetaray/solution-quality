"""List all available deployments in Azure OpenAI resource."""

import os
import requests
from dotenv import load_dotenv

def list_azure_deployments():
    """List all deployments available in the Azure OpenAI resource."""
    
    print("="*80)
    print("Listing Azure OpenAI Deployments")
    print("="*80)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not api_key or not endpoint:
        print("❌ Error: AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set")
        return False
    
    # Remove trailing slash from endpoint
    endpoint = endpoint.rstrip('/')
    
    # Try multiple API endpoints for listing deployments
    urls_to_try = [
        f"{endpoint}/openai/deployments?api-version={api_version}",
        f"{endpoint}/openai/models?api-version={api_version}",
    ]
    
    headers = {
        "api-key": api_key
    }
    
    print(f"\nTrying different API endpoints...\n")
    
    print(f"\nEndpoint: {endpoint}")
    print(f"API Version: {api_version}")
    print(f"\nTrying different API endpoints...\n")
    
    for url in urls_to_try:
        print(f"Trying: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for deployments in various response formats
                deployments = []
                if "data" in data:
                    deployments = data["data"]
                elif isinstance(data, list):
                    deployments = data
                elif "value" in data:
                    deployments = data["value"]
                
                if len(deployments) > 0:
                    print("\n✅ Available Deployments:")
                    print("="*80)
                    
                    for deployment in deployments:
                        # Handle different response formats
                        name = deployment.get("id") or deployment.get("name") or deployment.get("deployment_id", "N/A")
                        model = deployment.get("model") or deployment.get("model_name", "N/A")
                        status = deployment.get("status", "N/A")
                        
                        print(f"\n  Deployment Name: {name}")
                        print(f"  Model: {model}")
                        if status != "N/A":
                            print(f"  Status: {status}")
                        print("-"*80)
                    
                    print(f"\n✅ Found {len(deployments)} deployment(s)")
                    print("\nUpdate your .env file with one of these deployment names:")
                    print("AZURE_OPENAI_DEPLOYMENT=<deployment-name>")
                    
                    return True
                else:
                    print(f"  Status {response.status_code} but no deployments found")
                    continue
                    
            else:
                print(f"  Status {response.status_code}: {response.text[:100]}")
                continue
                
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
            continue
    
    # If we get here, none of the endpoints worked
    print("\n❌ Could not retrieve deployments from any API endpoint")
    print("\n⚠️  Please check deployments manually:")
    print("1. Go to https://oai.azure.com/")
    print("2. Select your 'hackathon-qa' resource")
    print("3. Click 'Deployments' in the left menu")
    print("4. Look for the 'Name' column - that's your deployment name")
    print("\nThen update .env with:")
    print("AZURE_OPENAI_DEPLOYMENT=<the-name-you-see>")
    
    return False


if __name__ == "__main__":
    success = list_azure_deployments()
    exit(0 if success else 1)
