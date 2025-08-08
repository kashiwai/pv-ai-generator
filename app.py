#!/usr/bin/env python3
"""
Ultra-minimal Gradio app to test HF Spaces deployment
"""

import gradio as gr
import os

print("===== Starting Ultra-Minimal Test =====")

def simple_function(text):
    """Simple test function"""
    if not text:
        return "Please enter some text"
    return f"You entered: {text}"

# Create the simplest possible Gradio app
print("Creating Gradio interface...")

iface = gr.Interface(
    fn=simple_function,
    inputs=gr.Textbox(label="Input"),
    outputs=gr.Textbox(label="Output"),
    title="Ultra-Minimal Test App",
    description="Testing basic Gradio functionality"
)

print("Interface created successfully")

if __name__ == "__main__":
    print("Launching app...")
    
    # Check if running on HF Spaces
    is_spaces = os.getenv("SPACE_ID") is not None
    
    if is_spaces:
        print("Detected HF Spaces environment")
        iface.launch(server_name="0.0.0.0", server_port=7860)
    else:
        print("Running in local environment")
        iface.launch()