# Security Policy

## Reporting a Vulnerability
If you discover a security vulnerability within this project, please report it to us immediately. We take all security reports seriously. (Note: Add a contact method here if this were a public project).

## Credential Management
This application requires Facebook credentials (username/email and password) to perform automation tasks. These are handled as follows:

*   **Environment Variables:** The primary method for providing credentials to the `automation_script` is through environment variables:
    *   `FB_USER`: Your Facebook username or email.
    *   `FB_PASS`: Your Facebook password.
*   **NEVER Hardcode Credentials:** Do not hardcode your Facebook username or password directly into any script or configuration file within this project. Hardcoding credentials is a significant security risk.
*   **Secure Your Environment:** Ensure that the environment where you set these variables is secure. If running on a shared system or server, restrict access to these variables.

## Session Token Storage (Future Consideration)
Currently, the application logs in fresh for each session or operation that requires it. If, in the future, the application is modified to store and reuse Facebook session tokens:

*   **Encryption at Rest:** Any session tokens or sensitive authentication data stored by the application **must be encrypted at rest**. This means using strong encryption algorithms to protect the file or database where these tokens might be stored.
*   **Secure Storage:** The storage mechanism itself must be secured against unauthorized access.

## General Security Practices
*   Keep your Facebook account secure with a strong, unique password and enable two-factor authentication (2FA).
*   Be aware of Facebook's terms of service regarding automation. Excessive or abusive automation can lead to account restrictions.
*   Regularly review and update dependencies of this project to patch known vulnerabilities.

## CAPTCHA Handling
This automation script is not designed to bypass or automatically solve CAPTCHAs presented by Facebook. Attempting to programmatically defeat CAPTCHAs can be unreliable, may violate Facebook's Terms of Service, and could involve security risks if using untrusted third-party solving services.

**If you encounter frequent CAPTCHAs:**

*   **Reduce Automation Speed:** Excessive or rapid automated actions are more likely to trigger CAPTCHAs. Ensure human-like delays are implemented and consider increasing them.
*   **Vary Interaction Patterns:** If the script performs the same actions repeatedly in the exact same way, it may be flagged.
*   **Consider Proxy Services:** Using a reputable proxy service might help, as your IP address could be temporarily flagged. However, choose proxy services carefully, as unreliable ones can pose their own security risks.
*   **Manual Intervention:** You may need to log in to your Facebook account manually in a regular browser to clear any pending CAPTCHAs or security checks.
*   **Script Behavior:** The script may attempt to detect common indicators of a CAPTCHA page. If detected, it will log a specific warning and the current operation (e.g., login, comment) will likely fail. It will not attempt to solve the CAPTCHA.

**We explicitly advise AGAINST:**

*   Integrating third-party automated CAPTCHA-solving services directly into this script, especially those requiring you to share credentials or API keys that could be misused.
