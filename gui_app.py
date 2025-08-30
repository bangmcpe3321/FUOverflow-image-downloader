import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import threading
import queue
import time
import re
import requests
import json
from PIL import Image
import getpass
import google.generativeai as genai

# Selenium Imports for Browser Automation
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- Constants and Configuration ---
CONFIG_FILE = "config.txt"
COOKIE_FILE = "cookies.json"
DOWNLOAD_DIRECTORY = "downloaded_images"

# --- Core Logic ---

def sanitize_filename(filename):
    """Removes invalid characters from a string to make it a valid filename."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename).strip()

def download_file_with_retry(image_url, filepath, cookies, headers, max_retries, retry_delay, log_queue):
    filename = os.path.basename(filepath)
    for attempt in range(max_retries):
        try:
            response = requests.get(image_url, cookies=cookies, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            log_queue.put(f"DOWNLOADER:[SUCCESS] Downloaded {filename}\n")
            return True
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            log_queue.put(f"DOWNLOADER:[ATTEMPT {attempt + 1}/{max_retries}] Failed for {filename}. Error: {e}\n")
            if attempt + 1 < max_retries:
                time.sleep(retry_delay)
            else:
                log_queue.put(f"DOWNLOADER:[FAILURE] All {max_retries} attempts failed for {filename}.\n")
    return False

def parse_url_pattern(url):
    pattern = re.compile(r"/([^/]+)\.(\d+)/?$")
    match = pattern.search(url)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def get_answer_from_image_with_gemini(image_path, prompt, api_key, log_queue, max_retries=3, retry_delay=5):
    """Sends an image and prompt to the Gemini model with a retry mechanism."""
    filename = os.path.basename(image_path)
    for attempt in range(max_retries):
        try:
            genai.configure(api_key=api_key)
            img = Image.open(image_path)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([prompt, img])
            return response.text, None
        except Exception as e:
            log_queue.put(f"PROCESSOR:  -> [ATTEMPT {attempt + 1}/{max_retries}] Failed for {filename}. Error: {e}\n")
            if attempt + 1 < max_retries:
                time.sleep(retry_delay)
            else:
                log_queue.put(f"PROCESSOR:  -> [FAILURE] All {max_retries} attempts failed for {filename}.\n")
                return None, f"All attempts failed. Last error: {e}"
    return None, "An unknown error occurred after all retries."

# --- GUI Application Class ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FUOverflow image downloader")
        self.geometry("800x600")

        self.log_queue = queue.Queue()

        self.tabControl = ttk.Notebook(self)
        self.downloader_tab = ttk.Frame(self.tabControl)
        self.processor_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.downloader_tab, text='Image Downloader')
        self.tabControl.add(self.processor_tab, text='Gemini Processor')
        self.tabControl.pack(expand=1, fill="both")

        self.create_downloader_widgets()
        self.create_processor_widgets()
        
        self.load_cookies()
        
        self.after(100, self.process_log_queue)

    def process_log_queue(self):
        while not self.log_queue.empty():
            try:
                message = self.log_queue.get_nowait()
                if "DOWNLOADER:" in message:
                    self.downloader_log.insert(tk.END, message.replace("DOWNLOADER:", ""))
                    self.downloader_log.see(tk.END)
                elif "PROCESSOR:" in message:
                    self.processor_log.insert(tk.END, message.replace("PROCESSOR:", ""))
                    self.processor_log.see(tk.END)
            except queue.Empty:
                pass
        self.after(100, self.process_log_queue)

    # --- Downloader Tab Methods ---
    def create_downloader_widgets(self):
        frame = self.downloader_tab
        
        input_frame = ttk.LabelFrame(frame, text="Download Configuration", padding=(10, 5))
        input_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(input_frame, text="Subject Code:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.subject_code_entry = ttk.Entry(input_frame, width=20)
        self.subject_code_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.subject_code_entry.insert(0, "ITE302c")
        
        ttk.Label(input_frame, text="Total Files:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.total_files_entry = ttk.Entry(input_frame)
        self.total_files_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(input_frame, text="xf_user Cookie:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.xf_user_entry = ttk.Entry(input_frame, width=60)
        self.xf_user_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(input_frame, text="xf_session Cookie:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.xf_session_entry = ttk.Entry(input_frame, show="*")
        self.xf_session_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Start URL (auto-filled):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.start_url_entry = ttk.Entry(input_frame, width=60, state="readonly")
        self.start_url_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        input_frame.columnconfigure(1, weight=1)
        
        self.download_button = ttk.Button(frame, text="Fetch URL and Start Download", command=self.start_unified_download_thread)
        self.download_button.pack(padx=10, pady=10)
        
        log_frame = ttk.LabelFrame(frame, text="Log", padding=(10, 5))
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.downloader_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12)
        self.downloader_log.pack(fill="both", expand=True)

    # --- Cookie Management Methods ---
    def load_cookies(self):
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, "r") as f:
                    cookies = json.load(f)
                    self.xf_user_entry.insert(0, cookies.get("xf_user", ""))
                    self.xf_session_entry.insert(0, cookies.get("xf_session", ""))
                self.log_queue.put("DOWNLOADER:Loaded saved cookies.\n")
            except (json.JSONDecodeError, IOError) as e:
                self.log_queue.put(f"DOWNLOADER:Could not load cookie file: {e}\n")

    def save_cookies(self):
        cookies_to_save = {
            "xf_user": self.xf_user_entry.get(),
            "xf_session": self.xf_session_entry.get()
        }
        try:
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies_to_save, f, indent=4)
            self.log_queue.put("DOWNLOADER:Cookies saved for next session.\n")
        except IOError as e:
            self.log_queue.put(f"DOWNLOADER:Could not save cookies: {e}\n")

    # --- Unified Download Process ---
    def start_unified_download_thread(self):
        self.download_button.config(state="disabled")
        self.downloader_log.delete(1.0, tk.END)
        self.start_url_entry.config(state="normal")
        self.start_url_entry.delete(0, tk.END)
        self.start_url_entry.config(state="readonly")
        
        thread = threading.Thread(target=self.run_unified_process, daemon=True)
        thread.start()

    def run_unified_process(self):
        subject_code = self.subject_code_entry.get()
        xf_user = self.xf_user_entry.get()
        xf_session = self.xf_session_entry.get()
        total_files_str = self.total_files_entry.get()

        if not all([subject_code, total_files_str, xf_user, xf_session]):
            messagebox.showerror("Error", "All fields are required.")
            self.after(0, lambda: self.download_button.config(state="normal"))
            return
            
        try:
            total_files = int(total_files_str)
        except ValueError:
            messagebox.showerror("Error", "Total files must be a valid number.")
            self.after(0, lambda: self.download_button.config(state="normal"))
            return

        self.save_cookies()

        self.log_queue.put("DOWNLOADER:--- Step 1: Fetching Start URL ---\n")
        start_url, thread_title = self.fetch_url_with_login(subject_code, xf_user, xf_session)

        if not start_url:
            self.log_queue.put("DOWNLOADER:[FATAL] Failed to fetch the start URL. Halting process.\n")
            self.after(0, lambda: self.download_button.config(state="normal"))
            return
        
        def update_url_entry():
            self.start_url_entry.config(state="normal")
            self.start_url_entry.delete(0, tk.END)
            self.start_url_entry.insert(0, start_url)
            self.start_url_entry.config(state="readonly")
        self.after(0, update_url_entry)
        
        self.log_queue.put("\nDOWNLOADER:--- Step 2: Starting Batch Download ---\n")
        self.run_downloader(start_url, total_files, {'xf_user': xf_user, 'xf_session': xf_session}, thread_title)

    def fetch_url_with_login(self, subject_code, xf_user, xf_session):
        driver = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--log-level=3")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            self.log_queue.put("DOWNLOADER:Logging in with cookies...\n")
            driver.get("https://fuoverflow.com/")
            driver.add_cookie({"name": "xf_user", "value": xf_user})
            driver.add_cookie({"name": "xf_session", "value": xf_session})
            
            forum_url = f"https://fuoverflow.com/forums/{subject_code}/"
            self.log_queue.put(f"DOWNLOADER:Navigating to subject forum: {forum_url}\n")
            driver.get(forum_url)
            
            self.log_queue.put("DOWNLOADER:Looking for the first thread title on the page...\n")
            thread_selector = "div.structItem--thread .structItem-title a[data-xf-init='preview-tooltip']"
            first_thread = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, thread_selector)))

            thread_title_raw = first_thread.text
            thread_title = sanitize_filename(thread_title_raw)
            self.log_queue.put(f"DOWNLOADER:Found thread: '{thread_title_raw}'. Clicking...\n")
            driver.execute_script("arguments[0].click();", first_thread)
            
            self.log_queue.put("DOWNLOADER:Looking for the first attachment...\n")
            attachment_selector = ".message-attachments .attachmentList a.file-preview"
            first_attachment = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, attachment_selector)))

            image_url = first_attachment.get_attribute('href')
            self.log_queue.put("DOWNLOADER:Success! Found attachment URL.\n")
            return image_url, thread_title

        except TimeoutException:
            page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
            if "you do not have permission" in page_text:
                self.log_queue.put("DOWNLOADER:[ERROR] 'Permission Denied' error detected. Cookies are likely expired.\n")
                messagebox.showerror("Automation Error", "Login Failed: 'Permission Denied'. Please update your cookies.")
            else:
                self.log_queue.put(f"DOWNLOADER:[ERROR] Timed out finding a thread or attachment in '{subject_code}' forum.\n")
                messagebox.showerror("Automation Error", f"Could not find a thread or attachment for '{subject_code}'. The forum/thread may be empty or your cookies are invalid.")
            return None, None
        except Exception as e:
            self.log_queue.put(f"DOWNLOADER:[ERROR] An unexpected error occurred: {e}\n")
            messagebox.showerror("Error", f"An unexpected error occurred during URL fetching. Check the log for details.")
            return None, None
        finally:
            if driver:
                driver.quit()

    def run_downloader(self, start_url, total_files, cookies, thread_title):
        base_name, start_id = parse_url_pattern(start_url)
        if base_name is None:
            messagebox.showerror("Error", "Could not parse the fetched URL pattern.")
            self.after(0, lambda: self.download_button.config(state="normal"))
            return
            
        self.log_queue.put(f"DOWNLOADER:Parsed URL. Base name: {base_name}, Start ID: {start_id}\n")
        
        download_path = os.path.join(DOWNLOAD_DIRECTORY, thread_title)
        os.makedirs(download_path, exist_ok=True)
        self.log_queue.put(f"DOWNLOADER:Saving images to folder: {download_path}\n")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        successful, skipped, failed_urls = 0, 0, []
        
        for i in range(total_files):
            current_id = start_id + i
            file_url = f"https://fuoverflow.com/attachments/{base_name}.{current_id}/"
            filename = f"{base_name}.{current_id}.webp"
            filepath = os.path.join(download_path, filename)
            
            if os.path.exists(filepath):
                self.log_queue.put(f"DOWNLOADER:[SKIPPED] {filename} already exists.\n")
                skipped += 1
                continue

            self.log_queue.put(f"DOWNLOADER:Downloading {filename}...\n")
            if download_file_with_retry(file_url, filepath, cookies, headers, 4, 5, self.log_queue):
                successful += 1
            else:
                failed_urls.append(file_url)
            time.sleep(0.5)

        self.log_queue.put(f"\nDOWNLOADER:--- Download Finished ---\n")
        self.log_queue.put(f"DOWNLOADER:Summary: {successful} downloaded, {skipped} skipped, {len(failed_urls)} failed.\n")
        
        if failed_urls:
            self.log_queue.put("DOWNLOADER:Failed URLs:\n" + "\n".join(failed_urls) + "\n")
            
        self.after(0, lambda: self.download_button.config(state="normal"))

    # --- Processor Tab Methods ---
    def create_processor_widgets(self):
        frame = self.processor_tab
        input_frame = ttk.LabelFrame(frame, text="Configuration", padding=(10, 5))
        input_frame.pack(padx=10, pady=10, fill="x")
        ttk.Label(input_frame, text="Gemini API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.api_key_entry = ttk.Entry(input_frame, width=60, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
            with open(CONFIG_FILE, "r") as f:
                self.api_key_entry.insert(0, f.read().strip())

        ttk.Label(input_frame, text="Image Directory:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dir_path_entry = ttk.Entry(input_frame, width=60)
        self.dir_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        browse_button = ttk.Button(input_frame, text="Browse...", command=self.browse_directory)
        browse_button.grid(row=1, column=2, padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)
        self.process_button = ttk.Button(frame, text="Start Processing", command=self.start_processing_thread)
        self.process_button.pack(padx=10, pady=5)
        log_frame = ttk.LabelFrame(frame, text="Log", padding=(10, 5))
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.processor_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.processor_log.pack(fill="both", expand=True)

    def browse_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_path_entry.delete(0, tk.END)
            self.dir_path_entry.insert(0, path)

    def start_processing_thread(self):
        self.process_button.config(state="disabled")
        self.processor_log.delete(1.0, tk.END)
        thread = threading.Thread(target=self.run_processor, daemon=True)
        thread.start()

    def run_processor(self):
        api_key = self.api_key_entry.get()
        image_dir = self.dir_path_entry.get()

        if not api_key or not image_dir:
            messagebox.showerror("Error", "API Key and Image Directory are required.")
            self.after(0, lambda: self.process_button.config(state="normal"))
            return

        if not os.path.isdir(image_dir):
            messagebox.showerror("Error", "The provided path is not a valid directory.")
            self.after(0, lambda: self.process_button.config(state="normal"))
            return

        with open(CONFIG_FILE, "w") as f:
            f.write(api_key)
        
        folder_name = os.path.basename(os.path.normpath(image_dir))
        sanitized_name = sanitize_filename(folder_name)
        output_txt_path = f"{sanitized_name}.txt"
        
        prompt = "Read the attached image. Extract every question you can find and provide a correct, concise answer for each one."
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

        self.log_queue.put(f"PROCESSOR:Processing images in: {image_dir}\n")
        self.log_queue.put(f"PROCESSOR:Results will be saved to: {output_txt_path}\n\n")

        try:
            with open(output_txt_path, "a", encoding="utf-8") as output_file:
                for filename in sorted(os.listdir(image_dir)):
                    if filename.lower().endswith(valid_extensions):
                        full_path = os.path.join(image_dir, filename)
                        self.log_queue.put(f"PROCESSOR:Processing image: {filename}...\n")
                        
                        # --- MODIFIED: Call the Gemini function with retry logic ---
                        answer, error = get_answer_from_image_with_gemini(full_path, prompt, api_key, self.log_queue)
                        
                        output_file.write(f"--- Question Source: {filename} ---\n")
                        if error:
                            self.log_queue.put(f"PROCESSOR:  -> FINAL ERROR: {error}\n")
                            output_file.write(f"An error occurred: {error}\n")
                        else:
                            self.log_queue.put(f"PROCESSOR:  -> Success.\n")
                            output_file.write(answer.strip() + "\n")
                        
                        output_file.write("\n" + "="*80 + "\n\n")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.after(0, lambda: self.process_button.config(state="normal"))
            return

        self.log_queue.put(f"PROCESSOR:\nBatch processing complete. Results appended to '{output_txt_path}'.\n")
        self.after(0, lambda: self.process_button.config(state="normal"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
