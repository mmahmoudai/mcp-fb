# Automation Script Setup

This directory contains the Python scripts for automating Facebook interactions.

## Environment Setup

To run the automation scripts, you'll need to set up a Python environment and install the required dependencies.

1.  **Create a virtual environment (recommended):**
    Open your terminal in the `automation_script` directory and run:
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

2.  **Install dependencies:**
    With the virtual environment activated, install the dependencies listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

Now you are ready to develop and run the automation scripts.

## Human-like Interaction Strategy

To make the automation appear more like human interaction and to help avoid detection by Facebook, the script incorporates random delays at various points:
- Before and between typing into input fields.
- Before clicking buttons or navigating to new pages.
- After actions, to simulate reading or reaction time.

These delays are randomized within a small range (typically between 0.5 to 3.5 seconds, with longer waits for page loads). While they can make the script slightly slower, they are important for responsible and potentially more stable automation.

## Security: Credential Handling

### Credential Handling

This script requires your Facebook username/email and password to function. For security reasons:

*   **Use Environment Variables:** Provide your credentials via the `FB_USER` and `FB_PASS` environment variables.
    ```bash
    export FB_USER="your_facebook_email@example.com"
    export FB_PASS="your_facebook_password"
    ```
*   **DO NOT hardcode your credentials directly into the `main.py` script or any other file.**
*   Ensure the environment where you set these variables is secure.

Refer to the main `SECURITY.md` file in the project root for more detailed security information.

### CAPTCHA Handling

This script does not automatically solve CAPTCHAs. If Facebook presents a CAPTCHA, the script will likely fail the current operation.

Frequent CAPTCHAs might indicate that your automation is being detected. Consider:
*   Slowing down the script's actions by adjusting the random delays mentioned in the "Human-like Interaction Strategy" section.
*   Logging in manually via a browser to clear any security checks.

Refer to the main `SECURITY.MD` file for a more detailed discussion on CAPTCHA handling and security implications.
