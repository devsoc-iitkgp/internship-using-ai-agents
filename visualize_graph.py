import sys
import os

# Add the current directory to python path to ensure imports work correctly
sys.path.append(os.getcwd())

# --- MOCKING PLAYWRIGHT ---
from unittest.mock import MagicMock
mock_playwright = MagicMock()
sys.modules["playwright"] = mock_playwright
sys.modules["playwright.async_api"] = mock_playwright
# --------------------------

try:
    from src.graph.workflow import create_workflow
    
    print("Creating workflow...")
    app = create_workflow()
    
    print("Generating graph visualization...")
    try:
        # Try to generate PNG directly
        # draw_mermaid_png requires an internet connection to use the mermaid.ink API 
        # or local dependencies.
        png_bytes = app.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Successfully saved visualization to 'workflow_graph.png'")
    except Exception as e:
        print(f"Could not generate PNG (likely due to missing dependencies or network issues): {e}")
        print("Falling back to Mermaid syntax...")
        # Fallback to text
        mermaid_text = app.get_graph().draw_mermaid()
        with open("workflow_graph.mmd", "w") as f:
            f.write(mermaid_text)
        print("Saved Mermaid syntax to 'workflow_graph.mmd'. You can view it at https://mermaid.live/")

except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure you are running this from the project root.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
