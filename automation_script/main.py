import os
import time
import random
import logging # Added for logging
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
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler('automation.log') # Corrected path: Logs will be in the script's CWD
# Console Handler
console_handler = logging.StreamHandler()

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add Handlers to Logger
if not logger.handlers: # Avoid adding multiple handlers if script is re-run in some contexts
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
# --- End Logging Setup ---

def login_facebook(driver, username, password):
    """Logs into Facebook using the provided username and password."""
    logger.info(f"Attempting Facebook login for user: {username}")
    try:
        login_url = "https://www.facebook.com/login/"
        logger.info(f"Navigating to login page: {login_url}")
        driver.get(login_url)

        email_selector = (By.ID, "email")
        pass_selector = (By.ID, "pass")
        login_button_selector = (By.NAME, "login")

        logger.info(f"Waiting for email input field: {email_selector}")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(email_selector)
        )
        logger.info("Email input field found. Sending username.")
        email_field.send_keys(username)

        logger.info(f"Finding password input field: {pass_selector}")
        pass_field = driver.find_element(*pass_selector)
        logger.info("Password input field found. Sending password.")
        pass_field.send_keys(password) # Do not log password itself

        logger.info(f"Finding and clicking login button: {login_button_selector}")
        login_button = driver.find_element(*login_button_selector)
        login_button.click()
        logger.info("Login button clicked.")

        time.sleep(5) # Allow time for page redirect and load

        current_url = driver.current_url
        logger.info(f"Current URL after login attempt: {current_url}")
        if "facebook.com/home.php" in current_url or \
           ("facebook.com/" == current_url and "login" not in current_url and "checkpoint" not in current_url) :
            logger.info("Login successful based on URL.")
            return True
        elif "login/" in current_url or "checkpoint" in current_url:
            logger.warning("Login failed or checkpoint encountered based on URL.")
            return False
        else:
            # Check for a common logged-in element as a fallback
            banner_selector = (By.XPATH, "//div[@role='banner']")
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located(banner_selector))
                logger.info("Login likely successful (found banner element).")
                return True
            except TimeoutException:
                logger.warning("Login failed. Could not confirm login status from URL or common page elements.")
                return False

    except TimeoutException as e:
        logger.error(f"Timeout occurred during login process: {e}", exc_info=True)
        return False
    except NoSuchElementException as e:
        logger.error(f"Could not find an element during login: {e}", exc_info=True)
        return False
    except ElementNotInteractableException as e:
        logger.error(f"Element not interactable during login: {e}", exc_info=True)
        return False
    except WebDriverException as e:
        logger.error(f"WebDriverException occurred during login: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during login: {e}", exc_info=True)
        return False

def search_facebook(driver, query):
    """Searches Facebook for posts matching the query."""
    logger.info(f"Initiating Facebook search for query: '{query}'")
    posts_content = []
    try:
        search_url = f"https://www.facebook.com/search/posts/?q={query}"
        logger.info(f"Navigating to search URL: {search_url}")
        driver.get(search_url)

        body_selector = (By.TAG_NAME, "body")
        logger.info(f"Waiting for search page body to load: {body_selector}")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(body_selector))
        logger.info("Search page body loaded. Waiting for dynamic content...")
        time.sleep(10) # Allow time for dynamic content

        post_article_xpath = "//div[@role='article']"
        post_pagelet_xpath = "//div[contains(@data-pagelet, 'FeedUnit_') or contains(@data-pagelet, 'Tahoe')]"

        logger.info(f"Attempting to find post elements using XPath: {post_article_xpath}")
        post_elements = driver.find_elements(By.XPATH, post_article_xpath)

        if not post_elements:
            logger.info(f"No elements found with role='article'. Trying fallback XPath: {post_pagelet_xpath}")
            post_elements = driver.find_elements(By.XPATH, post_pagelet_xpath)

        if not post_elements:
            logger.warning("No posts found matching the selectors. The page structure might have changed or no results for query.")
            return []

        logger.info(f"Found {len(post_elements)} potential post elements.")
        for i, post_element in enumerate(post_elements):
            try:
                post_text = post_element.text
                if post_text and post_text.strip():
                    posts_content.append(post_text)
                    logger.debug(f"Post {i+1} text extracted (first 100 chars): {post_text[:100]}...")
                else:
                    logger.debug(f"Post {i+1} found, but no visible text extracted directly.")
            except Exception as e_text:
                logger.error(f"Could not extract text from post element {i+1}: {e_text}", exc_info=True)

        logger.info(f"Extracted content from {len(posts_content)} posts.")
        return posts_content

    except TimeoutException as e:
        logger.error(f"Timeout occurred while waiting for search results page: {e}", exc_info=True)
        return []
    except WebDriverException as e:
        logger.error(f"WebDriverException occurred during search: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during search: {e}", exc_info=True)
        return []

def comment_on_post(driver, post_url, comment_text):
    """Navigates to a post and attempts to comment on it."""
    logger.info(f"Attempting to comment on post: {post_url}")
    try:
        logger.info(f"Navigating to post URL: {post_url}")
        driver.get(post_url)

        comment_box_xpath = "//div[@aria-label='Write a comment']|//div[@aria-label='Write a public comment...']|//div[@contenteditable='true' and @role='textbox']"
        logger.info(f"Waiting for comment input field using XPath: {comment_box_xpath}")
        comment_input_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, comment_box_xpath))
        )
        logger.info("Comment input field found.")

        logger.info("Clicking comment input field and typing comment.")
        comment_input_field.click()
        time.sleep(random.uniform(0.5, 1.5))
        comment_input_field.send_keys(comment_text) # Do not log comment_text if it can be sensitive
        logger.info(f"Typed comment text into field.")


        time.sleep(random.uniform(1, 3))

        submit_button_xpath = "//button[@aria-label='Comment']|//button[@aria-label='Post']|//button[.//span[text()='Post']]"
        logger.info(f"Locating comment submit button using XPath: {submit_button_xpath}")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
        )
        logger.info("Comment submit button found.")

        # THE ACTUAL CLICK
        submit_button.click()
        logger.info("Clicked comment submit button.")

        time.sleep(random.uniform(2, 5))

        current_url = driver.current_url
        if post_url in current_url: # Basic check
            logger.info("Comment submitted successfully (based on URL remaining consistent).")
            return True
        else:
            logger.warning(f"Comment submission might have failed (URL changed from {post_url} to {current_url}).")
            return False

    except TimeoutException as e:
        logger.error(f"Timeout occurred while trying to find an element for commenting on {post_url}: {e}", exc_info=True)
        return False
    except NoSuchElementException as e:
        logger.error(f"Could not find an element for commenting on {post_url}: {e}", exc_info=True)
        return False
    except ElementNotInteractableException as e:
        logger.error(f"Element not interactable while commenting on {post_url}: {e}", exc_info=True)
        return False
    except WebDriverException as e:
        logger.error(f"WebDriverException occurred during commenting on {post_url}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during commenting on {post_url}: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Facebook automation script started.")
    fb_user = os.environ.get("FB_USER")
    fb_pass = os.environ.get("FB_PASS")

    if not fb_user or not fb_pass:
        logger.error("Error: FB_USER and FB_PASS environment variables must be set.")
        exit(1)
    else:
        logger.info("FB_USER environment variable found.")
        # Do not log fb_pass

    driver = None
    placeholder_post_url = "https://www.facebook.com/Meta/posts/pfbid02QZJQ7f8YfG8XwQjXJqzZ6jZJ8XwQjXJqzZ6jZJ8XwQjXJqzZ6jZJ8XwQjXJqzZ6"
    test_comment_text = "This is an automated test comment via Selenium!" # Example, might be sensitive

    try:
        logger.info("Setting up Chrome WebDriver.")
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("WebDriver initialized.")

        login_success = login_facebook(driver, fb_user, fb_pass)

        if login_success:
            logger.info("Login successful. Proceeding with further actions.")

            # --- Optional: Perform a search ---
            # search_query = "metaverse"
            # logger.info(f"Starting search for query: '{search_query}'")
            # posts = search_facebook(driver, search_query)
            # if posts:
            #     logger.info(f"Search found {len(posts)} posts.")
            #     # for i, post_text in enumerate(posts):
            #     #     logger.debug(f"--- Post {i+1} ---\n{post_text[:200]}...")
            # else:
            #     logger.info("No posts found for the search query.")
            # time.sleep(2)

            # --- Attempt to comment on a post ---
            logger.info(f"Attempting to comment on placeholder post URL: {placeholder_post_url} with text: '{test_comment_text}'") # Log comment text if not sensitive
            comment_success = comment_on_post(driver, placeholder_post_url, test_comment_text)

            if comment_success:
                logger.info("Comment posting process completed successfully.")
            else:
                logger.warning("Comment posting process failed or status unknown.")

            time.sleep(5)
        else:
            logger.warning("Login failed. Cannot proceed with further actions.")

    except WebDriverException as e:
        logger.critical(f"A WebDriverException occurred in the main execution block, browser might have crashed or failed to start: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"An critical error occurred in the main execution block: {e}", exc_info=True)
    finally:
        if driver:
            logger.info("Closing browser.")
            driver.quit()
        logger.info("Facebook automation script finished.")
