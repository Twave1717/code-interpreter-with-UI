import subprocess
import threading
import time
import queue
import gradio as gr

def run_command_and_stream_output(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, text=True)

    q = queue.Queue()
    t = threading.Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True  # Thread dies with the program
    t.start()

    output = ""
    buffer = ""
    while True:
        try:
            char = q.get_nowait()
        except queue.Empty:
            time.sleep(0.1)
            continue

        if char == "" and process.poll() is not None:
            break

        buffer += char
        yield buffer
        if buffer.endswith("> ") or buffer.endswith("Execute the code? (Y/N): "):  # Detect the '> ' or '(Y/N)' prompt
            output += buffer
            yield output
            break

        if char == "\n":
            output += buffer
            yield output
            buffer = ""

def enqueue_output(out, q):
    while True:
        char = out.read(1)
        if char:
            q.put(char)
        else:
            break
    out.close()

def gradio_interface(command):
    return run_command_and_stream_output(command)

def on_click(command):
    current_output = ""
    for out in gradio_interface(command):
        current_output = out
        yield gr.update(value=current_output)

def on_click_rm():
    return ""

# Gradio Interface
with gr.Blocks() as demo:
    command = gr.Textbox(label="Command", value="python interpreter.py -md code -m gpt-3.5-turbo -dc")
    output = gr.Textbox(label="Output", lines=20, interactive=False)
    run_button = gr.Button("Run Command")

    run_button.click(on_click, inputs=command, outputs=output)
    run_button.click(on_click_rm, outputs=command)

demo.launch()
