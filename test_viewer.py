"""
Test viewer to display confidential data file
Run this alongside main.py to test blur detection
"""
import tkinter as tk
from tkinter import font

def main():
    root = tk.Tk()
    root.title("Test Confidential Data - Check Blur Detection")
    root.geometry("900x700")
    
    # Read the test file
    with open("test_confidential.txt", "r") as f:
        content = f.read()
    
    # Create text widget with custom font
    text_widget = tk.Text(root, wrap=tk.WORD, font=("Courier", 10))
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Insert content
    text_widget.insert(1.0, content)
    text_widget.config(state=tk.DISABLED)  # Read-only
    
    # Add instructions at the top
    instructions = tk.Label(
        root, 
        text="IMPORTANT: Run main.py in another window. All HIGHLIGHTED text below should be BLURRED in the screen recording.\nIf you see these values clearly in the recording, the blur detection needs adjustment.",
        fg="red",
        font=("Arial", 9, "bold"),
        wraplength=850,
        justify=tk.LEFT
    )
    instructions.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
