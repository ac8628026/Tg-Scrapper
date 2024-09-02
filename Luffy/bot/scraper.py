from .models import DownloadedFile
import os
import requests
from bs4 import BeautifulSoup
import socket
import re
import json
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time 
from django.core.cache import cache
from asgiref.sync import sync_to_async
# Set up the WebDriver


download_dir = r'E:\Projects\Scrapper_Bot\episodes' 
# chrome_options = Options()
# chrome_options.add_experimental_option('prefs', {
#     "download.default_directory": download_dir,
#     "download.prompt_for_download": False,
#     "directory_upgrade": True,
#     "safebrowsing.enabled": True
# })
options = webdriver.ChromeOptions()
options.add_argument("--disable-popup-blocking")
options.add_argument("--start-maximized")
prefs = {"download.default_directory": download_dir}
options.add_experimental_option("prefs", prefs)
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service,options=options)

# expected_filename = None
def is_file_downloaded(download_dir, filename):
    files = os.listdir(download_dir)
    return any(file == filename for file in files)

def close_new_tabs(driver, original_window):
    while len(driver.window_handles) > 1:
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                driver.close()
                print("New tab was closed.")
        driver.switch_to.window(original_window)

def click_download_button_js(xpath):
    try:
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].click();", element)
        print("Download button clicked via JavaScript.")
        # Wait for the download to start
        time.sleep(5)
        # etract the name of the most recent file being downloaded
        files = os.listdir(download_dir)
        file_name = None
        for file in files:
            if file.endswith('.crdownload'):
              #update the file_name with the file without the .crdownload extension
              file_name = file.replace('.crdownload', '')
              print(f"Downloading: {file_name}")
            break
        return True, file_name
    except Exception as e:
        print(f"Failed to click the download button via JavaScript: {e}")
        return False

#upload the file to the database
@sync_to_async
def upload_file_to_db(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
        file_name = os.path.basename(file_path)
        downloaded_file = DownloadedFile(filename=file_name, file_data=file_data)
        downloaded_file.save()
        print(f"File '{file_name}' uploaded to the database.")
    except Exception as e:
        print(f"Failed to upload file to the database: {e}")

@sync_to_async
def get_file_from_db(file_name):
    try:
        downloaded_file = DownloadedFile.objects.get(filename=file_name)
        "Fetched the file from database."
        return downloaded_file.file_data
    except DownloadedFile.DoesNotExist:
        print(f"File '{file_name}' not found in the database.")
        return None
    except Exception as e:
        print(f"Failed to retrieve file from the database: {e}")
        return None

def test_dns_resolution(domain):
    try:
        host = socket.gethostbyname(domain)
        print(f"Resolved IP address for {domain}: {host}")
        return True
    except socket.gaierror as e:
        print(f"DNS resolution failed for {domain}: {e}")
        return False

def fetch_anime_search_results(anime_name):
    cache_key = f'anime_search_results:{anime_name}'
    start_time = time.time()
    cached_results = cache.get(cache_key)
    if cached_results:
        end_time = time.time() 
        print("Returning cached data for the search results.", anime_name)
        print(f"Cached Latency: {end_time - start_time} seconds")
        return cached_results
    domain = "yugenanime.tv"
    if not test_dns_resolution(domain):
        return None
    search_url = f"https://{domain}/discover?q={anime_name.replace(' ', '+')}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    print(f"Search URL: {search_url}")
    soup = BeautifulSoup(response.content, 'html.parser')
    # extract from the <a> tag with class ="anime-meta" the href and title
    anime_link = soup.find('a', class_="anime-meta")
    if not anime_link:
        print(f"Anime '{anime_name}' not found in search results.")
        return None
    #iterate through all results and return all the elements with title and href
    anime_results = []
    for anime in soup.find_all('a', class_="anime-meta"):
        anime_results.append((anime['href'], anime['title']))
    cache.set(cache_key, anime_results, timeout=60*60)  #set the cache for 1 hour for now
    end_time = time.time()
    print(f"Uncached Latency: {end_time - start_time} seconds")
    return anime_results

#fetch season and its episodes
def fetch_anime_details(anime_url):
    cache_key = f'anime_details_{anime_url}'
    start_time = time.time()
    cached_details = cache.get(cache_key)
    if cached_details:
        end_time = time.time()
        print("Returning cached data for the anime.", anime_url)
        print(f"Cached Latency: {end_time - start_time} seconds")
        return cached_details
    #this url doesn't contain the domain name so we need to add it
    domain = "yugenanime.tv"
    anime_url = f"https://{domain}{anime_url}"
    #first go the the webpage and take the http response from it 
    try:
        response = requests.get(anime_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch anime page: {e}")
        return None
    #use the scraper to scrape the data
    soup = BeautifulSoup(response.content, 'html.parser')
    # print(soup.prettify()
    #I will move to the watch page and extract the episodes 
    # to first get to the watch page it is inside the <div> with class = navigation and the second a tag has the link
    watch_page = soup.find('div', class_="navigation").find_all('a')[1]['href']
    watch_page = f"https://{domain}{watch_page}"
    #now we take the HTML from this page
    try:
        response = requests.get(watch_page)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch watch page: {e}")
        return None
    #use the scraper to scrape the data
    soup = BeautifulSoup(response.content, 'html.parser')
    #extract the episodes and title from the <a> tag with class = "ep-title"
    episodes = []
    for episode in soup.find_all('a', class_="ep-title"):
        episodes.append((episode['href'], episode['title']))
    cache.set(cache_key, episodes, timeout=60*60)  #set the cache for 1 hour for now
    end_time = time.time()  # End timing
    print(f"Uncached Latency: {end_time - start_time} seconds")
    return episodes

# use the episode link to download the anime to database
async def download_anime(episode_url):
    cache_key = f'anime_download_{episode_url}'
    start_time = time.time()
    cached_data = await cache.aget(cache_key)
    if cached_data:
        end_time = time.time()
        print("Returning cached data for the episode.", episode_url)
        print(f"Cached Latency: {end_time - start_time} seconds")
        return io.BytesIO(cached_data)
    domain = "yugenanime.tv"
    episode_url = f"https://{domain}{episode_url}"
    try:
        response = requests.get(episode_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch episode page: {e}")
        return None
    #use the scraper to scrape
    soup = BeautifulSoup(response.content, 'html.parser')
    #extract the download link from <a name="player-download" href="https://embtaku.pro/download?id=MTQ4NTMy" target="_blank" class="btn"></a>
    download_link = soup.find('a', class_="btn", target="_blank")
    if not download_link:
        print("Download link not found on episode page.")
        return None
    use_link = download_link['href']
    print(use_link)

    #use selenium to go to the webpage
    driver.get(use_link)
    original_window = driver.current_window_handle

    try:
        # download_button = WebDriverWait(driver, 20).until(
        #     EC.presence_of_element_located((By.XPATH, download_button_xpath))
        # )
        download_button_xpath = '//*[@id="content-download"]/div[1]/div[1]/a'
        print("Download button is present in the DOM.")

        attempts = 0
        max_attempts = 5
        file_name = None
        downloading = False
        while attempts < max_attempts:
            print("Attempt no ", attempts+1)
            try:
                WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, download_button_xpath))
                )
                downloading, file_name = click_download_button_js(download_button_xpath)
                print("Is downloading", downloading)
                if downloading:
                    break
            except Exception as e:
                print(f"Failed to click the download button: {e}")
            attempts += 1
            close_new_tabs(driver, original_window)
            time.sleep(5)  # Wait before the next attempt
    
        if attempts == max_attempts:
            print("Failed to click the download button after multiple attempts.")
            driver.close()
            exit()

        # Wait for a while to ensure the download starts
        # time.sleep(5)
        # Monitor download progress
        timeout = 300  # Maximum time to wait in seconds (5 minutes)
        start_time = time.time()
        download_started = False
        #check if the file is already present in the database
        print(f"Checking if file '{file_name}' already exists in the database.")
        existing_file = await get_file_from_db(file_name)
        if existing_file:
            print(f"File '{file_name}' already exists in the database.")
            #stop downloading in the chrome but do not close the driver 
            driver.close()
            #remove the downloading file from the directory
            files = os.listdir(download_dir)
            for file in files:
                if file.startswith(file_name):
                    os.remove(os.path.join(download_dir, file))
            #return the file from the database
            # need to convert the existing_file data to bytes file is a memoryview and django cache 
            #framework uses serialization(pickle) to store the data in cache, memoryview objects cannot be pickeld
            #This happens when we try to cache binary data directly so we need to convert this into bytes
            bytes_data = bytes(existing_file)  
            await cache.aset(cache_key, bytes_data, timeout=60*60*24)
            print("Set the cache for 1 day for the file.", file_name)
            end_time = time.time()
            print(f"Uncached Latency: {end_time - start_time} seconds")
            return io.BytesIO(existing_file)

        while downloading:


            # Check if the file has started downloading
            if is_file_downloaded(download_dir, file_name):
                print("Download completed!")
                #upload this file to the database with the name of the anime and the name of the episode from the requests

                await upload_file_to_db(os.path.join(download_dir, file_name))
                file_data = await get_file_from_db(file_name)
                print("DONE FOR THE BACKEND PART")
                #delete the file from the directory 
                bytes_data = bytes(file_data)
                await cache.aset(cache_key, bytes_data, timeout=60*60*24)
                os.remove(os.path.join(download_dir, file_name))
                # return file_data
                end_time = time.time()  # End timing
                print(f"Uncached Latency: {end_time - start_time} seconds")
                return io.BytesIO(file_data)
            files = os.listdir(download_dir)
            for file in files:
                if file_name and file.startswith(file_name) and file.endswith('.crdownload'):
                    print("Download is in progress...")
                    if not download_started:
                        download_started = True

            # Check if the file has been downloaded
            if time.time() - start_time > timeout:
                print("Timeout: Download not completed within the expected time.")
                downloading = False
            time.sleep(1)  # Wait 1 second before checking again
    except Exception as e:
        print(f"Failed to download anime: {e}")
        return None

#get all the files from db
def get_all_files_from_db():
    files = DownloadedFile.objects.all()
    if not files:
        print("No files found in the database.")
        return None
    for file in files:
        print(file.filename)
    return None

# retireve the file from the database using the name of the file



export = {
    "fetch_anime_search_results": fetch_anime_search_results,
    "fetch_anime_details": fetch_anime_details,
    "download_anime": download_anime,
    "get_all_files_from_db": get_all_files_from_db,
    "get_file_from_db": get_file_from_db
}































# def fetch_anime_search_results(anime_name):
#     domain = "ripcrabbyanime.com"
    
#     if not test_dns_resolution(domain):
#         return None
#     search_url = f"https://{domain}/search/?s={anime_name.replace(' ', '+')}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed: {e}")
#         return None
#     print(f"Search URL: {search_url}")
#     print(f"Response Status Code: {response.status_code}")
#     soup = BeautifulSoup(response.content, 'html.parser')

#     # Find the <a> tag containing the anime title
#     anime_link = soup.find('a', text=re.compile(anime_name, re.IGNORECASE))
#     if not anime_link:
#         print(f"Anime '{anime_name}' not found in search results.")
#         return None

#     anime_page_url = anime_link['href']
#     print(f"Anime page URL: {anime_page_url}")
#     return anime_page_url

# def fetch_anime_page(anime_page_url):
#     try:
#         response = requests.get(anime_page_url)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         print(f"Failed to fetch anime page: {e}")
#         return None

#     return response.content

# def list_available_seasons(anime_page_content):
#     soup = BeautifulSoup(anime_page_content, 'html.parser')
#     # print(soup.prettify())
#     season_buttons = soup.find_all('button', text=re.compile(r"Season", re.IGNORECASE))

#     seasons = {}
#     for i, button in enumerate(season_buttons):
#         parent_div = button.find_parent('div')
#         if parent_div:
#             anchor = parent_div.find('a', href=True)
#             if anchor:
#                 seasons[i+1] = (button.text, anchor['href'])

#     if not seasons:
#         print("No seasons found on anime page.")
#         return None


#     return seasons
#     # print("Available seasons:")
#     # for num, (text, _) in seasons.items():
#     #     print(f"{num}. {text}")


# ##    DO NOT TOUCH THE ABOVE CODE    ##
# ##   DO NOT TOUCH THE ABOVE CODE    ##
# ##  DO NOT TOUCH THE ABOVE CODE    ##
# ## DO NOT TOUCH THE ABOVE CODE    ##
# ## DO NOT TOUCH THE ABOVE CODE    ##


# # def choose_season(seasons):
# #     while True:
# #         try:
# #             choice = int(input("Enter the number of the season you want to download: "))
# #             if choice in seasons:
# #                 return seasons[choice][1]
# #             else:
# #                 print("Invalid choice. Please try again.")
# #         except ValueError:
# #             print("Invalid input. Please enter a number.")

# # def fetch_google_drive_link(season_url):
# #     try:
# #         response = requests.get(season_url)
# #         response.raise_for_status()
# #         # print(response.content)
# #     except requests.exceptions.RequestException as e:
# #         print(f"Failed to fetch season page: {e}")
# #         return None

# #     soup = BeautifulSoup(response.content, 'html.parser')
# #     # print(soup.prettify())
# #     gdrive_link = soup.find('a', href=re.compile(r'drive.google.com', re.IGNORECASE))

# #     if gdrive_link:
# #         return gdrive_link['href']
# #     else:
# #         print("Google Drive link not found on the season page.")
# #         return None

# def get_anime_seasons(anime_name):
#     anime_page_url = fetch_anime_search_results(anime_name)
#     if not anime_page_url:
#         return None

#     anime_page_content = fetch_anime_page(anime_page_url)
#     if not anime_page_content:
#         return None

#     seasons = list_available_seasons(anime_page_content)
#     if not seasons:
#         return None

#     # season_url = choose_season(seasons)
#     # if not season_url:
#     #     return None

#     # download_link = fetch_google_drive_link(season_url)
#     # return download_link
#     if(not seasons):
#         return None
#     return seasons

# # def get_hianime_download_link(anime_name):
# #     domain = "ripcrabbyanime.com"
    
# #     if not test_dns_resolution(domain):
# #         return None
# #     search_url = f"https://{domain}/search/?s={anime_name.replace(' ', '+')}"
# #     try:
# #         response = requests.get(search_url)
# #         print(response.text)
# #         response.raise_for_status()
# #     except requests.exceptions.RequestException as e:
# #         print(f"Request failed: {e}")
# #         return None

# #     print(f"Search URL: {search_url}")
# #     print(f"Response Status Code: {response.status_code}")

# #     soup = BeautifulSoup(response.content, 'html.parser')

# #     # Find the <a> tag containing the anime title
# #     anime_link = soup.find('a', text=re.compile(anime_name, re.IGNORECASE))
# #     if not anime_link:
# #         print(f"Anime '{anime_name}' not found in search results.")
# #         return None

# #     anime_page_url = anime_link['href']
# #     print(f"Anime page URL: {anime_page_url}")

# #     # Now, fetch the anime page to find the download link
# #     try:
# #         anime_response = requests.get(anime_page_url)
# #         anime_response.raise_for_status()
# #         # print(anime_response)
# #     except requests.exceptions.RequestException as e:
# #         print(f"Failed to fetch anime page: {e}")
# #         return None

# #     anime_soup = BeautifulSoup(anime_response.content, 'html.parser')

# #     # Example: Find the download link assuming it's inside a <div> with class 'download-link'
# #     season_link = anime_soup.find('a', href=re.compile(r'drive.google.com', re.IGNORECASE))
# #     if not season_link:
# #         print("Season link not found on anime page.")
# #         return None

# #     season_page_url = season_link['href']
# #     print(f"Season page URL: {season_page_url}")

# #     try:
# #         season_response = requests.get(season_page_url)
# #         season_response.raise_for_status()
# #     except requests.exceptions.RequestException as e:
# #         print(f"Failed to fetch season page: {e}")
# #         return None

# #     season_soup = BeautifulSoup(season_response.content, 'html.parser')

# #     # Example: Find the Google Drive download link assuming it's inside a <a> with a specific pattern
# #     drive_link = season_soup.find('a', href=re.compile(r'drive.google.com', re.IGNORECASE))
# #     if not drive_link:
# #         print("Google Drive download link not found on season page.")
# #         return None

# #     download_url = drive_link['href']
# #     print(f"Google Drive download link: {download_url}")

# #     return download_url

# def fetch_google_drive_folder_page(folder_url):
#     try:
#         response = requests.get(folder_url)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         print(f"Failed to fetch Google Drive folder page: {e}")
#         return None

#     return response.content

# def extract_files_from_script(script_content):
#     # Use regex to find the JSON-like structure inside the script content
#     if('AF_initDataCallback' not in script_content):
#         return []
#     match = re.search(r'AF_initDataCallback\((.*?)\);', script_content, re.DOTALL)
#     if not match:
#         return []

#     # Extract the matched group which contains the data
#     script_data = match.group(1)
    
#     # Find the JSON data within the script content
#     json_match = re.search(r'data:([\s\S]*), sideChannel:', script_data)
#     if not json_match:
#         return []

#     # Parse the JSON data
#     json_data = json.loads(json_match.group(1))

#     # Extract file details
#     files = []
#     for file_data in json_data[1]:
#         file_id = file_data[0]
#         file_name = file_data[2]
#         mime_type = file_data[3]
#         file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drive_web"
        
#         files.append({
#             "file_name": file_name,
#             "mime_type": mime_type,
#             "file_url": file_url
#         })

#     return files


# def list_files_in_drive_folder(folder_url):
#     folder_page_content = fetch_google_drive_folder_page(folder_url)
#     if not folder_page_content:
#         return None

#     # soup = BeautifulSoup(folder_page_content, 'html.parser')
#     # Extract the JavaScript content that contains the file details
#     # script_tags = soup.find_all('script')
#     # for i, script_tag in enumerate(script_tags):
#     #     print(f"Script tag {i}:")
#     #     print(script_tag.string)
#     #     print("\n\n")
#     # script_tag = soup.find('script', text=re.compile(r'window\["_DRIVE_ivd"\]'))
#     # if not script_tag:
#     #     print("No JavaScript content found with file details.")
#     #     return None

#     # js_content = script_tag.string

#     # files = extract_files_from_js(js_content)
#     #use the soup library to extract the tags with div and class = Q5txwe and jsname = wuLfrd
#     soup = BeautifulSoup(folder_page_content, 'html.parser')
    
#     # Find the script tag containing the file details
#     script_tags = soup.find('script', {'nonce': True})
#     script_content = script_tags.string
#     for script in script_tags:
#         print(script.string)
#         if 'AF_initDataCallback' in script.string:
#             print(script)
#             return extract_files_from_script(script.string)
    
#     return []
