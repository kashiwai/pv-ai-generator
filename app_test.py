"""
Gradio compatibility test for HF Spaces
Testing basic Gradio functionality without complex components
"""
import gradio as gr
import os

def test_function(text):
    return f"Received: {text}"

with gr.Blocks() as demo:
    gr.Markdown("# Test Gradio App")
    
    with gr.Row():
        input_text = gr.Textbox(label="Input")
        output_text = gr.Textbox(label="Output")
    
    btn = gr.Button("Test")
    btn.click(fn=test_function, inputs=input_text, outputs=output_text)

if __name__ == "__main__":
    is_spaces = os.getenv("SPACE_ID") is not None
    
    if is_spaces:
        print("Running on HF Spaces")
        demo.launch(server_name="0.0.0.0", server_port=7860)
    else:
        print("Running locally")
        demo.launch()