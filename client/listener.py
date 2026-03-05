import keyboard
import pyperclip
import requests
import time
import traceback
import sys

API_URL = "http://127.0.0.1:8000/api/generate-doc"
HOTKEY = "ctrl+alt+d"

def trigger_documentation():
    print(f"\n[Client] Hotkey '{HOTKEY}' pressed. Starting process...")
    try:
        # 1. Copy highlighted text via Ctrl+C
        keyboard.send("ctrl+c")
        time.sleep(0.3) # Give OS time to update clipboard
        
        # 2. Extract from clipboard
        code_snippet = pyperclip.paste()
        
        if not code_snippet or not code_snippet.strip():
            print("[Client] No text was copied to clipboard.")
            return

        print(f"[Client] Copied {len(code_snippet)} characters. Sending to backend...")
        
        # 3. Send to FastAPI backend
        response = requests.post(API_URL, json={"code_snippet": code_snippet})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print("[Client] Successfully triggered documentation generation! Ghost-typing should start momentarily.")
            else:
                print(f"[Client] Backend reported error: {data.get('message')}")
        else:
            print(f"[Client] Failed to connect to server. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"[Client] Error during trigger execution: {e}")
        traceback.print_exc()

def listen_for_hotkey():
    print(f"Ghost-Typer Client Listener starting...")
    print(f"Make sure the FastAPI server is running on {API_URL}")
    print(f"Waiting for global hotkey: '{HOTKEY}'")
    print("Press Ctrl+C in this terminal to exit.")
    
    # suppress=True prevents other applications from processing the hotkey
    keyboard.add_hotkey(HOTKEY, trigger_documentation, suppress=True) 
    
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nExiting listener...")
        sys.exit(0)

if __name__ == "__main__":
    listen_for_hotkey()
