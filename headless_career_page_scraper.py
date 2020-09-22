#Jacob Pawlak
#career_page_scraper.py
#april 30th, 2020
#goooo blue team!

######################### IMPORTS #########################

#importing my 2 web scraping libraries, as ya do
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
#since i have some free credits on my twilio account, I am going to use an sms service to send me the links to the job descriptions i want to see
from twilio.rest import Client
#standard libs
import time


######################### HELPERS #########################

#a quick, like 2 line helper to just send a message over twilio's api
#https://www.twilio.com/docs/libraries/python
def send_text_msg(to_num, from_num, body_text, client):

    #quick little message sending method that i found from the twilio python docs.
    message = client.messages.create(to=to_num, from_=from_num, body=body_text)
    return message.sid


#this little helper function is meant to pull out the location, link and title of the job
#only gets called in the list comp inside the scrape_jobs() function
def extract_job(job_div):

    ##pulling out the title, location, and link from the list item 'job_div'
    job_title = job_div.find('span', attrs={'class': 'resultHeader'}).text.strip()
    job_loc = job_div.find('span', attrs={'class': 'hiringPlace'}).text.strip()
    job_link = job_div.find('a')['href']
    #really only need the louisville job openings rn, ill adjust this as needed
    if(job_loc == "Louisville, Kentucky"):
        #i really only want the links to local jobs, dont need the other ones, so ill return this tuple if i find a local job...
        # and 0 if i dont
        return (job_title, 'https://brown-forman.jobs{}'.format(job_link))
    return 0


#the helper function i am going to do all of the scraping in. i have my target site, and a pretty good idea of the data i want to pull out and return
def scrape_jobs():

    #we are going to return a list of jobs and links to the job description
    #an example might look like ("software engineer", "https://brown-forman.jobs/usacanada/new-jobs/")
    jobs_and_links = []

    #target url: https://brown-forman.jobs/usacanada/new-jobs/
    target_url = "https://brown-forman.jobs/usacanada/new-jobs/"

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    #time to go scrape the page, gotta make the chrome driver
    driver = webdriver.Chrome('./Chrome/83/chromedriver', options=chrome_options)
    driver.get(target_url)
    time.sleep(3)

    #just incase there are more jobs in the queue as the freeze opens up
    while(True):
        try:
            #look for the more jobs button, and click it if we find it, then wait to see if there are still more jobs
            driver.find_element_by_id("button_moreJobs")
            more_button = driver.find_element_by_id("button_moreJobs")
            more_button.click()
            print("clicked the more button")
            time.sleep(3)
        #if there isnt a more jobs button on the page, then we are clear to pull the page source
        except (NoSuchElementException, ElementNotInteractableException) as err:
            print("no more more button, {}".format(err))
            break

    #this next line will grab the active page source from the driver and put it into a bs4 object for me to pull data out of
    soup = BeautifulSoup(driver.page_source, 'html5lib')
    job_listings = soup.find_all('li', attrs={'class': 'direct_joblisting'})
    #cute little list comprehension that will be used to fill the 
    [jobs_and_links.append(extract_job(job_listing)) for job_listing in job_listings]

    driver.quit()

    #clearing out the zeros
    while(0 in jobs_and_links):
        jobs_and_links.remove(0)

    return jobs_and_links

######################### MAIN () #########################

def main():

    #since there are some important auth keys needed for the twilio part, i dont want to hardcode those into my program - i am going to use a datafile (classic me)
    #i dont expect many people to see this so forgive me for using a file name literal, but i dont think anyone will actually want to clone this repo so idc
    data_file = open('datafile.json', 'r')
    data_list = []
    #pulling out the json object in the file and transforming it to a dictionary
    for line in data_file:
        data_list = eval(line)
    data_list = data_list[0]

    #now that we have the auth keys and stuff from the data file pulled in, lets set up the twilio client
    client = Client(str(data_list['account_sid']), str(data_list['auth_token']))

    #now it is time to scrape the page, so ill make a call to the helper function
    jobs_and_links = scrape_jobs()
    #i didnt want to have to do it like this but i couldnt get the += to work inside the list comprehension i made
    body_text = ""
    messages = []

    for job_and_link in jobs_and_links:
        if(len(body_text) > 1400):
            messages.append(body_text)
            body_text = ""
        body_text += "{} - {}\n".format(job_and_link[0], job_and_link[1])
    messages.append(body_text)

    [send_text_msg(str(data_list['to_number']), str(data_list['from_number']), str(body_text), client) for body_text in messages]
    #this is a call to the helper function when we are ready to send the text message
    #message = send_text_msg(str(data_list['to_number']), str(data_list['from_number']), str(body_text), client)

    return

main()
