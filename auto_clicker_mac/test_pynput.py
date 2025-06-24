# test_pynput.py
import time
import platform

print(f"Python Version: {platform.python_version()}")
print(f"Platform: {platform.platform()}")
print(f"Machine: {platform.machine()}")

print("\nAttempting to import pynput.keyboard...")
try:
    from pynput import keyboard
    print("pynput.keyboard imported successfully.")
except Exception as e:
    print(f"Error importing pynput.keyboard: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit()

def on_press(key_event):
    print("[test_pynput] Key pressed event received.")
    try:
        print(f"  Key char: {key_event.char}")
    except AttributeError:
        print(f"  Special key: {key_event}")
    # Stop listener after 1 key press for this test
    return False

def on_release(key_event):
    # print(f"Key released: {key_event}") # Optional
    pass

print("\nAttempting to start pynput.keyboard.Listener...")
print("Please press any key on your keyboard.")

try:
    # Collect events until on_press returns False
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        print("Listener instance created. Waiting for key press to trigger on_press...")
        listener.join() # This will block until the listener stops
    print("Listener finished and joined.")
except Exception as e:
    print(f"An error occurred with the pynput.Listener: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    if "rocess is not trusted" in str(e) or "AXUIElementCopyAttributeValue" in str(e) or "Input Monitoring" in str(e).lower() or "accessibility" in str(e).lower() :
        print("--------------------------------------------------------------------")
        print("macOS PERMISSION ISSUE: ")
        print("Please ensure Accessibility access AND Input Monitoring permissions are granted.")
        print("1. System Settings > Privacy & Security > Accessibility")
        print("   Add your Terminal/IDE to the list and ensure it's checked.")
        print("2. System Settings > Privacy & Security > Input Monitoring")
        print("   Add your Terminal/IDE to the list and ensure it's checked.")
        print("You MIGHT NEED TO RESTART your Terminal/IDE after changing these settings.")
        print("--------------------------------------------------------------------")

print("\nScript finished.")
