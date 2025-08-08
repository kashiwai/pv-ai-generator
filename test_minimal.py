#!/usr/bin/env python3
"""
Ultra-minimal Gradio test to isolate the issue
"""

import gradio as gr

def greet(name):
    return f"Hello, {name}!"

# Create the simplest possible interface
demo = gr.Interface(
    fn=greet,
    inputs="text",
    outputs="text",
    title="Minimal Test"
)

if __name__ == "__main__":
    demo.launch()