import os
from PIL import Image
import getpass
import google.generativeai as genai

# --- CONFIGURATION ---
CONFIG_FILE = "config.txt"

def load_or_request_api_key():
    """
    Loads the API key from the config file, or prompts the user if it doesn't exist.
    """
    # Check if the config file exists and has content
    if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
        print("API key found in config.txt. Using existing key.")
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    else:
        # Prompt the user for the key if the file doesn't exist
        print("API key not found. Please enter it now.")
        api_key = getpass.getpass("Enter your Google Gemini API Key: ")
        
        # Save the key to the file for future use
        try:
            with open(CONFIG_FILE, "w") as f:
                f.write(api_key)
            print(f"API key saved to {CONFIG_FILE} for future use.")
            return api_key
        except Exception as e:
            print(f"Warning: Could not save API key to file. You may be prompted again next time. Error: {e}")
            return api_key

def get_answer_from_image_with_gemini(image_path, prompt):
    """
    Sends a single image and a text prompt to the Gemini model.
    """
    try:
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt, img])
        return response.text, None
    except Exception as e:
        return None, f"An error occurred while processing {os.path.basename(image_path)}: {e}"

# --- MAIN SCRIPT EXECUTION ---
if __name__ == "__main__":
    print("--- Gemini Batch Image Processor ---")
    
    # 1. Load the API key from file or request it from the user
    api_key = load_or_request_api_key()
    if not api_key:
        print("Error: No API key was provided.")
        exit()
    
    # 2. Configure the Gemini client
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Error: Failed to configure the Gemini client. The provided API key may be invalid. Details: {e}")
        # Optional: Delete the bad key so the user is prompted next time
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("Removed invalid key from config.txt. Please run the script again.")
        exit()

    # 3. Get the path to the folder of images
    input_dir_path = input("\nEnter the path to the DIRECTORY containing your images: ")
    cleaned_path = input_dir_path.strip().strip('"\'')

    if not os.path.isdir(cleaned_path):
        print(f"Error: The provided path is not a valid directory.")
        exit()

    output_txt_path = "all_questions_and_answers.txt"
    prompt = "Read the attached image. Extract every question you can find and provide a correct, concise answer for each one."
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    print(f"\nProcessing images in: {cleaned_path}")
    print(f"Results will be saved to: {output_txt_path}\n")

    # 4. Process all images in the directory
    with open(output_txt_path, "a", encoding="utf-8") as output_file:
        for filename in os.listdir(cleaned_path):
            if filename.lower().endswith(valid_extensions):
                full_image_path = os.path.join(cleaned_path, filename)
                print(f"Processing image: {filename}...")

                answer, error = get_answer_from_image_with_gemini(full_image_path, prompt)

                output_file.write(f"--- Question Source: {filename} ---\n")
                if error:
                    print(f"  -> ERROR: {error}")
                    output_file.write(f"An error occurred: {error}\n")
                else:
                    print(f"  -> Success.")
                    output_file.write(answer.strip() + "\n")
                
                output_file.write("\n" + "="*80 + "\n\n")

                if i < total_files - 1:
                time.sleep(8)

    print(f"\nBatch processing complete. All results have been appended to '{output_txt_path}'.")
