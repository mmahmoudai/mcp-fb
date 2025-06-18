import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    WebDriverException
)
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# --- Logging Setup ---
logger = logging.getLogger(__name__) # This logger can be used by the backend if it imports this module
logger.setLevel(logging.INFO)
# File Handler
file_handler = logging.FileHandler('automation.log')
# Console Handler
console_handler = logging.StreamHandler()
# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
# --- End Logging Setup ---

class FacebookAutomator:
    def __init__(self):
        logger.info("Initializing FacebookAutomator...")
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless") # Optional: run in headless mode
            options.add_argument("--disable-notifications")
            options.add_argument("--start-maximized")
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")

            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("WebDriver initialized successfully.")
        except WebDriverException as e:
            logger.critical(f"WebDriver failed to initialize: {e}", exc_info=True)
            self.driver = None # Ensure driver is None if init fails
            raise # Re-raise the exception to signal failure to the caller

    def _check_for_captcha(self):
        if not self.driver:
            return False # Cannot check without a driver

        # Basic check for keywords that might indicate a captcha page
        page_title = ""
        page_source_sample = ""
        try:
            page_title = self.driver.title.lower()
            # Get a sample of the page source to avoid performance issues with very large pages
            page_source_sample = self.driver.page_source[0:4000].lower()
        except WebDriverException as e:
            logger.warning(f"Could not retrieve page title or source for CAPTCHA check: {e}")
            return False # Unsure, assume no CAPTCHA

        captcha_keywords = ['captcha', 'security check', 'are you human', 'verify your account', 'unusual activity', 'confirm your identity']

        if any(keyword in page_title for keyword in captcha_keywords):
            logger.warning("Potential CAPTCHA detected based on page title: %s", self.driver.title)
            return True

        if any(keyword in page_source_sample for keyword in captcha_keywords):
            logger.warning("Potential CAPTCHA detected based on page content keywords (first 4000 chars).")
            return True

        # Example for specific iframe (can be added if a common pattern is identified)
        # try:
        #     if self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]"):
        #         logger.warning("Potential reCAPTCHA iframe detected.")
        #         return True
        # except NoSuchElementException:
        #     pass

        return False

    def login(self, username=None, password=None):
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot attempt login.")
            return False

        fb_user = username or os.environ.get('FB_USER')
        fb_pass = password or os.environ.get('FB_PASS')

        if not fb_user or not fb_pass:
            logger.error("FB_USER or FB_PASS environment variables not found, and no credentials provided to login method.")
            return False

        logger.info(f"Attempting Facebook login for user: {fb_user}")
        try:
            login_url = "https://www.facebook.com/login/"
            logger.info(f"Navigating to login page: {login_url}")
            self.driver.get(login_url)
            time.sleep(random.uniform(0.5, 1.5)) # Delay after page load

            email_selector = (By.ID, "email")
            pass_selector = (By.ID, "pass")
            login_button_selector = (By.NAME, "login")

            logger.info(f"Waiting for email input field: {email_selector}")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(email_selector)
            )
            logger.info("Email input field found. Applying short delay before typing username.")
            time.sleep(random.uniform(0.6, 1.2))
            email_field.send_keys(fb_user)
            logger.info("Username sent.")

            logger.info(f"Finding password input field: {pass_selector}")
            pass_field = self.driver.find_element(*pass_selector)
            logger.info("Password input field found. Applying short delay before typing password.")
            time.sleep(random.uniform(0.5, 1.1))
            pass_field.send_keys(fb_pass)
            logger.info("Password sent.")

            logger.info(f"Finding and clicking login button: {login_button_selector}")
            login_button = self.driver.find_element(*login_button_selector)
            time.sleep(random.uniform(0.4, 0.9)) # Delay before click
            login_button.click()
            logger.info("Login button clicked.")

            logger.info("Waiting for page to load after login click (randomized delay).")
            time.sleep(random.uniform(3, 6)) # Randomized page load wait

            current_url = self.driver.current_url
            logger.info(f"Current URL after login attempt: {current_url}")
            if "facebook.com/home.php" in current_url or \
               ("facebook.com/" == current_url and "login" not in current_url and "checkpoint" not in current_url):
                logger.info("Login successful based on URL.")
                return True
            elif "login/" in current_url or "checkpoint" in current_url:
                logger.warning("Login failed or checkpoint encountered based on URL.")
                return False
            else:
                banner_selector = (By.XPATH, "//div[@role='banner']")
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(banner_selector))
                    logger.info("Login likely successful (found banner element).")
                    return True
                except TimeoutException:
                    logger.warning("Login failed. Could not confirm login status from URL or common page elements.")
                    if self._check_for_captcha():
                        logger.error("CAPTCHA detected after login attempt failed to find banner element. Manual intervention likely required.")
                    return False
            # After a click, if URL check fails, also check for CAPTCHA before returning False
            if self._check_for_captcha():
                 logger.error("CAPTCHA detected on page after login attempt. Manual intervention likely required.")
            return False
        except TimeoutException as e:
            logger.error(f"Timeout occurred during login: {e}", exc_info=True)
            if self._check_for_captcha():
                 logger.error("CAPTCHA detected after timeout during login. Manual intervention likely required.")
            return False
        except NoSuchElementException as e:
            logger.error(f"Could not find an element during login: {e}", exc_info=True)
            if self._check_for_captcha():
                 logger.error("CAPTCHA detected after NoSuchElementException during login. Manual intervention likely required.")
            return False
        except ElementNotInteractableException as e:
            logger.error(f"Element not interactable during login: {e}", exc_info=True)
            if self._check_for_captcha():
                 logger.error("CAPTCHA detected after ElementNotInteractableException during login. Manual intervention likely required.")
            return False
        except WebDriverException as e: # This is a broad category, could include page load issues
            logger.error(f"WebDriverException occurred during login: {e}", exc_info=True)
            if self._check_for_captcha(): # Check if the WebDriverException led to a CAPTCHA page
                 logger.error("CAPTCHA detected after WebDriverException during login. Manual intervention likely required.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during login: {e}", exc_info=True)
            # It's good practice to check for CAPTCHA even on unexpected errors if possible
            if self.driver: # Check if driver is still valid
                if self._check_for_captcha():
                    logger.error("CAPTCHA detected after an unexpected error during login. Manual intervention likely required.")
            return False

    def search(self, query):
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot attempt search.")
            return {"error": "WebDriver not initialized"}

        logger.info(f"Initiating Facebook search for query: '{query}'")
        posts_content = []
        try:
            search_url = f"https://www.facebook.com/search/posts/?q={query}"
            logger.info(f"Preparing to navigate to search URL: {search_url}")
            time.sleep(random.uniform(0.7, 1.8)) # Delay before navigation
            self.driver.get(search_url)
            logger.info(f"Navigated to search URL: {search_url}")

            body_selector = (By.TAG_NAME, "body")
            logger.info(f"Waiting for search page body to load: {body_selector}")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located(body_selector))
            logger.info("Search page body loaded. Waiting for dynamic content (e.g., posts).")
            # This existing sleep is for dynamic content, keep it, maybe randomize
            time.sleep(random.uniform(8, 12))

            logger.info("Simulating user pausing to view results before extraction.")
            time.sleep(random.uniform(1.5, 3.5)) # Pause before extraction

            post_article_xpath = "//div[@role='article']"
            post_pagelet_xpath = "//div[contains(@data-pagelet, 'FeedUnit_') or contains(@data-pagelet, 'Tahoe')]"

            logger.info(f"Attempting to find post elements using XPath: {post_article_xpath}")
            post_elements = self.driver.find_elements(By.XPATH, post_article_xpath)

            if not post_elements:
                logger.info(f"No elements found with role='article'. Trying fallback XPath: {post_pagelet_xpath}")
                post_elements = self.driver.find_elements(By.XPATH, post_pagelet_xpath)

            if not post_elements:
                logger.warning("No posts found for query.")
                return [] # Return empty list if no posts

            logger.info(f"Found {len(post_elements)} potential post elements.")
            for i, post_element in enumerate(post_elements):
                try:
                    post_text = post_element.text
                    if post_text and post_text.strip():
                        posts_content.append(post_text)
                        logger.debug(f"Post {i+1} text extracted (first 100 chars): {post_text[:100]}...")
                except Exception as e_text:
                    logger.error(f"Could not extract text from post element {i+1}: {e_text}", exc_info=True)

            logger.info(f"Extracted content from {len(posts_content)} posts.")
            return posts_content
        except TimeoutException as e:
            logger.error(f"Timeout occurred while waiting for search results: {e}", exc_info=True)
            return {"error": f"Timeout during search: {e}"}
        except WebDriverException as e:
            logger.error(f"WebDriverException occurred during search: {e}", exc_info=True)
            return {"error": f"WebDriver error during search: {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred during search: {e}", exc_info=True)
            return {"error": f"Unexpected error during search: {e}"}

    def comment(self, post_url, comment_text):
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot attempt comment.")
            return False

        logger.info(f"Attempting to comment on post: {post_url}")
        try:
            logger.info(f"Preparing to navigate to post URL: {post_url}")
            time.sleep(random.uniform(0.8, 2.0)) # Delay before navigation
            self.driver.get(post_url)
            logger.info(f"Navigated to post URL: {post_url}")
            time.sleep(random.uniform(1.0, 2.5)) # Delay for page elements to settle after navigation

            comment_box_xpath = "//div[@aria-label='Write a comment']|//div[@aria-label='Write a public comment...']|//div[@contenteditable='true' and @role='textbox']"
            logger.info(f"Waiting for comment input field: {comment_box_xpath}")
            comment_input_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, comment_box_xpath))
            )
            logger.info("Comment input field found.")

            time.sleep(random.uniform(0.5, 1.2)) # Delay before clicking comment box
            comment_input_field.click()
            logger.info("Clicked comment input field.")

            time.sleep(random.uniform(0.7, 1.5)) # Delay before typing comment
            comment_input_field.send_keys(comment_text)
            logger.info("Typed comment text into field.")
            time.sleep(random.uniform(1.5, 3.5)) # Delay after typing comment

            submit_button_xpath = "//button[@aria-label='Comment']|//button[@aria-label='Post']|//button[.//span[text()='Post']]"
            logger.info(f"Locating comment submit button: {submit_button_xpath}")
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
            )
            logger.info("Comment submit button found.")
            time.sleep(random.uniform(0.6, 1.3)) # Delay before clicking submit
            submit_button.click()
            logger.info("Clicked comment submit button.")

            logger.info("Waiting for comment to post (randomized delay).")
            time.sleep(random.uniform(3.0, 6.0)) # Wait for comment to post

            current_url = self.driver.current_url
            if post_url in current_url:
                logger.info("Comment submitted successfully (based on URL).")
                return True
            else:
                logger.warning(f"Comment submission might have failed (URL changed from {post_url} to {current_url}).")
                return False
        except TimeoutException as e:
            logger.error(f"Timeout occurred while commenting: {e}", exc_info=True)
            return False
        except NoSuchElementException as e:
            logger.error(f"Element not found while commenting: {e}", exc_info=True)
            return False
        except ElementNotInteractableException as e:
            logger.error(f"Element not interactable while commenting: {e}", exc_info=True)
            return False
        except WebDriverException as e:
            logger.error(f"WebDriverException occurred during commenting: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during commenting: {e}", exc_info=True)
            return False

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully.")
            except WebDriverException as e:
                logger.error(f"Error closing WebDriver: {e}", exc_info=True)
            finally:
                self.driver = None # Ensure driver is set to None

if __name__ == '__main__':
    logger.info("Starting Facebook Automation Script directly (for testing or direct execution).")
    automator = None
    try:
        automator = FacebookAutomator() # WebDriver is initialized here
        if automator.driver: # Check if driver was initialized successfully
            logger.info("FacebookAutomator initialized. Attempting login...")
            if automator.login(): # Uses env vars by default
                logger.info("Login successful (direct run).")
                # Example: Perform a search
                # posts = automator.search("example query")
                # logger.info(f"Search results (direct run): {posts}")

                # Example: Perform a comment (use with extreme caution and a test post)
                # placeholder_post_url = "https_your_test_post_url_here"
                # test_comment_text = "This is a direct run test comment."
                # if placeholder_post_url != "https_your_test_post_url_here": # Basic check
                #    comment_status = automator.comment(placeholder_post_url, test_comment_text)
                #    logger.info(f"Comment status (direct run): {comment_status}")
                pass # Kept simple for this refactoring step
            else:
                logger.warning("Login failed (direct run).")
        else:
            logger.error("FacebookAutomator could not be initialized with a driver.")

    except Exception as e:
        logger.critical(f"Critical error in direct execution: {e}", exc_info=True)
    finally:
        if automator:
            logger.info("Closing driver from direct execution block.")
            automator.close_driver()
    logger.info("Facebook Automation Script (direct run) finished.")
