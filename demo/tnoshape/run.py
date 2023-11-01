import gradio as gr


def process(x):
    return x


demo = gr.Interface(fn=process, inputs=[gr.TNOShape(label="Shape")], outputs=gr.Textbox(label="X"))

if __name__ == "__main__":
    demo.launch()
