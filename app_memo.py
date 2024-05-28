import subprocess
import threading
import time
import queue

def read_output(process, log_file, q):
    with open(log_file, 'a') as f:
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
            if buffer.endswith("> "):  # Detect the '> ' prompt
                print("Input prompt detected. Breaking loop.")
                break

            if buffer.endswith("(Y/N):"):  # Detect the '> ' prompt
                print("Input prompt detected. Breaking loop.")
                break

            if char == "\n":
                f.write(buffer)
                print(buffer, end="")
                buffer = ""

def enqueue_output(out, q):
    while True:
        char = out.read(1)
        if char:
            q.put(char)
        else:
            break
    out.close()

def run_command_and_log_output(command, log_file):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, text=True)

    q = queue.Queue()
    t = threading.Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True  # Thread dies with the program
    t.start()

    try:
        read_output(process, log_file, q)
    except KeyboardInterrupt:
        pass  # Handle user interrupt

    return process

def main():
    command = "python interpreter.py -md code -m gpt-3.5-turbo -dc"
    log_file = "command_log.txt"
    
    while True:
        try:
            process = run_command_and_log_output(command, log_file)
            
            # Wait for user input after detecting the prompt
            while True:
                user_input = input("> ")
                if user_input.strip().lower() == 'exit':
                    process.terminate()
                    process.wait()
                    print("Process terminated.")
                    return

                process.stdin.write(user_input + "\n")
                process.stdin.flush()
                read_output(process, log_file, queue.Queue())
                
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    main()
