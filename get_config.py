import requests, datetime
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import threading


def get_xml_domains(autoconfig_url):

    xml_domains = []
    response = requests.get(autoconfig_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        for link in links:
            xml_domains.append(link)
    else:
        print("Failed to retrieve data:", response.status_code)
    return xml_domains[5:]

def details(xml_domain, type):

    selection = {'smtp', 'pop3', 'imap'}  # Set of chosen values
    if type not in selection:
        raise ValueError(f"Error: {type} is not a valid value. Choose from {selection}.")
    file_lock = threading.Lock()

    try:
        response = requests.get(f"{autoconfig_url}{xml_domain}")
        response.raise_for_status()

        root = ET.fromstring(response.content)
        #domains = [elem.text for elem in root.findall('.//domain')]
       
        server = root.find(f'.//incomingServer[@type="{type}"]')
        if type == 'smtp':
            server = root.find(f'.//outgoingServer[@type="{type}"]')
        hostname = server.find('hostname').text
        port = server.find('port').text
        login_template = server.find('username').text

        #results = [f"{domain}:{hostname}:{port}:{login_template}" for domain in domains]
        print(f"fetching {xml_domain}")
        results = f"{xml_domain}:{hostname}:{port}:{login_template}"
        file_lock.acquire()

        with open(f'autoconfigs.txt', 'a') as file:
            #file.write('\n'.join(results) + '\n')
            file.write(f'{results}\n')
            print(results)
        
        with open(f'{type}.txt', 'a') as file:
            if type != 'smtp':
                file.write(f'{xml_domain}|{hostname}\n')
            else:
                file.write(f'{xml_domain}|{hostname}|{port}\n')


        file_lock.release()

    except requests.RequestException as e:
        print(f"Error fetching the XML: {e}")
    except ET.ParseError as e:
        print(f"Error parsing the XML: {e}")
    except AttributeError as e:
        print(f"{xml_domain} {type} does not exist.")
        pass



def get_details(type, xml_domains, num_threads):
    selection = {'smtp', 'pop3', 'imap'}  # Set of chosen values
    if type not in selection:
        raise ValueError(f"Error: {type} is not a valid value. Choose from {selection}.")
    

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(details, xml_domain, type): xml_domain for xml_domain in xml_domains}
        for future in futures:
            future.result()  # Wait for all threads to complete


def getAll(xml_domains):
    with open(f'autoconfigs.txt', 'w') as file:
        file.write(f'fetched from: {autoconfig_url}, updated at: {str(datetime.date.today())}\ndomain:smtp_host:smtp_port:smtp_login_template\n')
    print("Getting POP3")
    get_details( xml_domains=xml_domains,type='pop3', num_threads=1)
    print("Getting IMAP")
    get_details( xml_domains=xml_domains, type='imap', num_threads=1)
    print("Getting SMTP")
    get_details( xml_domains=xml_domains, type='smtp', num_threads=1)



def main():

    global autoconfig_url
    autoconfig_url = "https://autoconfig.thunderbird.net/v1.1/"
    
    #num_threads = int(input("Enter the number of threads to use: "))  # Input for number of threads
    #type = str(input("Enter type of extraction (smtp|pop3|imap): ")).lower()
    xml_domains = get_xml_domains(autoconfig_url)
    #get_details(type, xml_domains, num_threads)

    getAll(xml_domains)
    
    

if __name__ == '__main__':
    main()
