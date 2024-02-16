from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import requests
import time
import os
from datetime import datetime

CLIPS_DIRECTORY = 'clips'


def extract_clip_video_url(clip_url, channel_name):
    '''
        # Set up Selenium Chrome WebDriver
        options = Options()
        options.add_argument("--headless")  # Run headless
        service = Service('/path/to/chromedriver')  # Provide path to your chromedriver executable
        '''

    # possibly change to Chrome when it is supported

    firefox_options = Options()
    firefox_options.add_argument("--headless")

    driver = webdriver.Firefox(options=firefox_options)

    print("web driver started...")

    # Fetch the clip page
    driver.get(clip_url)

    # Wait for dynamic content to load (adjust wait time as needed)
    time.sleep(5)

    # Find video link element
    mp4_element = driver.find_element(By.XPATH, '//video')

    # Grab video source link
    clip_source_url = mp4_element.get_attribute('src')

    # Close the WebDriver
    driver.quit()

    if clip_source_url:
        print("Clip source URL:", clip_source_url)
    else:
        print("Failed to extract clip source URL.")

    try:
        video_response = requests.get(clip_source_url, stream=True)

        current_datetime = datetime.now()

        formatted_datetime = current_datetime.strftime("_%m_%d_%H_%M_%S")

        filename = 'clips/' + channel_name + formatted_datetime + '.mp4'

        if not os.path.exists(CLIPS_DIRECTORY):
            os.makedirs(CLIPS_DIRECTORY)

        if video_response.status_code == 200:

            # Open a new file in binary write mode
            with open(filename, 'wb') as f:
                # Iterate over the content of the response in chunks and write it to the file
                for chunk in video_response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"Video downloaded successfully as {filename}")
        else:
            print("Failed to download video: HTTP status code", video_response.status_code)
    except Exception as e:
        print("An error occurred:", e)
