from datetime import datetime
import os.path
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


auth = {
    'login'     :   ''      , # Account that has stats prividges (usually admin)
    'password'  :   ''

}

projects = [
    #('LBL-CoDEx' ,   'OpenSoCFabric') #, # Projects you want to scrape
    ('ucb-bar'   ,   'context-dependent-environments')
]

admins = [
    'ucbjrl@berkeley.edu'    # Who should get emailed in case something goes wrong
]

display = Display(visible=0, size=(800, 600))
display.start()
driver = webdriver.Firefox()


def scrapeTraffic(proj) :
    baseURL = 'https://github.com/'
    # clonesURL = baseURL + proj[0] + '/' + proj[1] + '/graphs/clone-activity-data'
    # trafficURL = baseURL + proj[0] + '/' + proj[1] + '/graphs/traffic-data'
    trafficTabURL = baseURL + proj[0] + '/' + proj[1] + '/graphs/traffic'
    
    driver.get("https://github.com/login")
    try :
        login = driver.find_element_by_name("login")
        login.send_keys(auth["login"])
        password = driver.find_element_by_name("password")
        password.send_keys(auth["password"])
        driver.find_element_by_name("commit").click()
        print "Logged to " + proj[0] + '/' + proj[1] + " as User: " + auth["login"]
    except NoSuchElementException as e:
        # Already logged in
        print "Already logged in to " + proj[0] + '/' + proj[1] + " as User: " + auth["login"]

    driver.get(trafficTabURL)
    
    CloneTot = ''
    CloneUnq = ''
    ViewsTot = ''
    ViewsUnq = ''
    try :
        CloneTot = driver.find_element_by_xpath('//*[@id="js-clones-graph"]/div/div[2]/ul/li[1]/span').text
        CloneUnq = driver.find_element_by_xpath('//*[@id="js-clones-graph"]/div/div[2]/ul/li[2]/span').text
        ViewsTot = driver.find_element_by_xpath('//*[@id="js-visitors-graph"]/div/div[2]/ul/li[1]/span').text
        ViewsUnq = driver.find_element_by_xpath('//*[@id="js-visitors-graph"]/div/div[2]/ul/li[2]/span').text
    except IndexError as e:
        print "You probably don't have access to that project: " + projTup2Str(proj)
        sendmail(proj)
        CloneTot = 'error'
        CloneUnq = 'error'
        ViewsTot = 'error'
        ViewsUnq = 'error'
                
    rtnVal = {
        'CloneTot'  :   CloneTot,
        'CloneUnq'  :   CloneUnq,
        'ViewsTot'  :   ViewsTot,
        'ViewsUnq'  :   ViewsUnq
    }
    
    return rtnVal

# print map(lambda x : (x, scrapeTraffic(x)), projects)

def sendmail(proj) :
    smtp = smtplib.SMTP('localhost')
    fromaddr = "github@codexhpc.org"#"github-cookies@socks.lbl.gov"
    toaddr = admins
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = COMMASPACE.join(toaddr)
    msg['Subject'] = "Github Connection Failure for " + projTup2Str(proj)
    now = datetime.now()
    body = "At " + now.strftime('%Y %b %d %H:%M:%S') + ", Github Connection for Python Scraper has failed for " + projTup2Str(proj) + ". Maybe you should give me a better cookie?\n"
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()
    smtp.sendmail(fromaddr, toaddr, text)
    smtp.close()

def projTup2Str(proj) :
    return proj[0] + "/" + proj[1]

def main() :
    for proj in projects :
        vals = scrapeTraffic(proj)
        date = datetime.now()
        filePath = os.path.dirname(os.path.realpath(__file__)) + '/'
        # print filePath
        fileName = date.strftime('%Y') + '_' + proj[0] + '_' + proj[1] + '.csv'
        if os.path.isfile(filePath + fileName):
            f = open(filePath + fileName, 'a')
        else :
            f = open(filePath + fileName, 'w')
            f.write('Date,Unique Clones,Total Clones,Unique Views,Total Views\n')
        f.write( date.strftime('%Y/%m/%d %H:%M:%S') + ',' +
            vals['CloneUnq'] + ',' +
            vals['CloneTot'] + ',' +
            vals['ViewsUnq'] + ',' +
            vals['ViewsTot'] + '\n'
            )
        f.close()
    driver.quit()
    display.stop()

if __name__ == '__main__':
    main()

