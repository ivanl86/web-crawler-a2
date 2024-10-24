import re
from urllib.parse import urlparse,urlunparse
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = extract_links(url, resp)
 
    extract_html_content(resp)

    return [link for link in links if is_valid(link)]

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    allowed_domains = [
        "ics.uci.edu",
        "cs.uci.edu",
        "informatics.uci.edu",
        "stat.uci.edu",
        "today.uci.edu"
    ]

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if parsed.netloc not in allowed_domains:
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def extract_links(url, resp):
    if resp.status != 200:
        return []
    
    if not resp.raw_response or not resp.raw_response.content:
        return []
    
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    ## start to find the a tag and extract the href content
    raw_links = []
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')

        if href:
            raw_links.append(href)

    clean_links = []
    for link in raw_links:
        parsed_link = urlparse(link)
        link_with_no_frag = urlunparse(
            (parsed_link.scheme, parsed_link.netloc, parsed_link.path, parsed_link.params, parsed_link.query, "")
        )
        clean_links.append(link_with_no_frag)


    return clean_links

def extract_html_content(resp):
    """
    Extract and print the content of the HTML page

    @TODO Need to be tokenized instead of printing to the console
    """
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    print(soup.get_text(separator=" ", strip=True))
