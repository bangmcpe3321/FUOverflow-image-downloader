# FUOverflow Image Downloader & Gemini Processor

This project provides a two-part utility for downloading images from `fuoverflow.com` and processing them using the Google Gemini AI to extract and answer questions found within the images.

## Features

- **Graphical User Interface**: A user-friendly GUI built with Tkinter for easy operation.
- **Image Downloader**: A dedicated tab to batch-download images, requiring a start URL and session cookies for authentication.
- **Gemini AI Processor**: A second tab to analyze a directory of images. It uses the Gemini AI to identify questions in each image and generate answers.
- **Command-Line Interface**: The AI processing logic can also be run as a standalone CLI script (`AI.py`).
- **Output Logging**: Both the downloader and processor log their progress in the GUI and save the final AI-generated answers to a `.txt` file.
- **Configuration Management**: Automatically loads and saves the required Google Gemini API key from a `config.txt` file.

---

## ⚠️ Security Warning

This project stores your Google Gemini API key in a plain text file (`config.txt`). To prevent accidentally sharing your secret API key, it is **strongly recommended** that you do not commit this file to a public repository.

Create a `.gitignore` file in the project's root directory with the following contents to exclude sensitive files and downloaded data from source control:

```
# Python virtual environment
/venv/

# Configuration files
config.txt
cookies.json

# Downloaded images
/downloaded_images/

# Output files
*.txt
```

---

## Prerequisites

- Python 3.12.x
- The following Python libraries:
  - `google-generativeai`
  - `requests`
  - `Pillow`
  - `selenium`
  - `webdriver-manager`

## Installation

**Windows:**
- Simply run `gui.bat` to start the application.

**Linux:**
1.  **Clone the repository (or download the files):**
    ```bash
    git clone https://github.com/bangmcpe3321/FUOverflow-image-downloader.git
    
    cd FUOverflow-image-downloader
    ```

2.  **Set up a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install google-generativeai requests Pillow selenium webdriver-manager
    ```

## How to Use

### GUI Method (Recommended)

Launch the application by running the batch file or the Python script:

- **Windows**: Double-click `gui.bat`
- **Linux**: Run `python gui_app.py` from your terminal.

#### 1. Image Downloader Tab

This tab is for downloading images from `fuoverflow.com`.

1.  **Subject Code**: Enter the subject code from the forum URL (e.g., `ITE302c`).
2.  **Total Files**: Enter the total number of images you want to download.
3.  **xf_user Cookie**: Enter your `xf_user` cookie value for authentication.
4.  **xf_session Cookie**: Enter your `xf_session` cookie value.
5.  Click **Fetch URL and Start Download**. The application will first automatically find the correct starting URL and then begin downloading the images into a folder named after the discussion thread's title inside the `downloaded_images` directory.

##### How to Get Your Cookies

**Chrome :**

  You can use a browser extension like [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) to easily view and copy the `xf_user` and `xf_session` cookie values.

**Firefox :**
1.  Open `fuoverflow.com` in Firefox.
2.  Press `F12` to open the developer tools.
3.  Go to the **Network** tab.
4.  Refresh the page (F5).
5.  Click on any request to `fuoverflow.com` in the list.
6.  In the right-hand panel, go to the **Cookies** tab.
7.  Find and copy the values for `xf_user` and `xf_session`.

#### 2. Gemini Processor Tab

This tab is for analyzing the downloaded images with AI.

1.  **Gemini API Key**: Your key from `config.txt` should be loaded automatically. You can also paste it here directly.
2.  **Image Directory**: Click **Browse...** and select the `downloaded_images` folder (or any other folder containing images you want to process).
3.  Click **Start Processing**. The AI will analyze each image, and the results will be appended to a `.txt` file named after the image directory (e.g., `downloaded_images.txt`).

### Command-Line Method (Processor Only)

You can run the AI analysis directly from the command line.

1.  Open your terminal in the project directory.
2.  Run the script:
    ```bash
    python AI.py
    ```
3.  The script will first check for an API key in `config.txt`. If not found, it will prompt you to enter it.
4.  It will then ask for the path to the directory containing your images.
5.  The script will process all images in the folder and save the results to `all_questions_and_answers.txt`.

---

## File Descriptions

- `gui_app.py`: The main application file containing the Tkinter-based GUI.
- `AI.py`: A standalone script for running the AI image processing from the command line.
- `gui.bat`: A batch script for easily launching the GUI application on Windows.
- `config.txt`: Configuration file to store the Google Gemini API key (auto-generated).
- `test.py`: A file for testing purposes.
