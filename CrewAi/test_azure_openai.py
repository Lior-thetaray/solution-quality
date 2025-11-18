"""Test Azure OpenAI connection and configuration."""

import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

def test_azure_openai_connection():
    """Test Azure OpenAI connection with a simple query."""
    
    print("="*80)
    print("Testing Azure OpenAI Connection")
    print("="*80)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    print("\nConfiguration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Deployment: {deployment}")
    print(f"  API Version: {api_version}")
    print(f"  API Key: {'*' * 20}{api_key[-8:] if api_key else 'NOT SET'}")
    
    # Validate configuration
    missing = []
    if not api_key:
        missing.append("AZURE_OPENAI_API_KEY")
    if not endpoint:
        missing.append("AZURE_OPENAI_ENDPOINT")
    if not deployment:
        missing.append("AZURE_OPENAI_DEPLOYMENT")
    
    if missing:
        print(f"\n❌ Error: Missing required environment variables: {', '.join(missing)}")
        print("\nPlease update your .env file with:")
        print("  AZURE_OPENAI_API_KEY=<your-api-key>")
        print("  AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.openai.azure.com/")
        print("  AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>")
        print("  AZURE_OPENAI_API_VERSION=2024-02-15-preview")
        return False
    
    # Test connection
    try:
        print("\n" + "="*80)
        print("Initializing Azure OpenAI client...")
        print("="*80)
        
        llm = AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        print("✅ Client initialized successfully")
        
        print("\n" + "="*80)
        print("Sending test query...")
        print("="*80)
        
        response = llm.invoke("Say 'Hello, Azure OpenAI is working!' in one sentence.")
        
        print("\n✅ Connection successful!")
        print(f"\nResponse: {response.content}")
        
        print("\n" + "="*80)
        print("Azure OpenAI is configured correctly and ready to use!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to Azure OpenAI:")
        print(f"   {type(e).__name__}: {str(e)}")
        print("\nCommon issues:")
        print("  1. Check your endpoint URL format: https://<resource-name>.openai.azure.com/")
        print("  2. Verify your deployment name matches Azure portal")
        print("  3. Confirm API key is correct")
        print("  4. Check if your Azure resource has quota available")
        import traceback
        print("\nFull error:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_azure_openai_connection()
    exit(0 if success else 1)
