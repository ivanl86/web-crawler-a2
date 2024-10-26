from datetime import datetime
import re
from urllib.parse import urlparse,urlunparse
from bs4 import BeautifulSoup

# A set of stop words that will be ignored when reading from pages
stop_word = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as',
             'at', 'be', 'because',
             'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't",
             'did', "didn't", 'do',
             'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had',
             "hadn't", 'has', "hasn't",
             'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself',
             'him', 'himself', 'his',
             'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its',
             'itself', "let's", 'me',
             'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or',
             'other', 'ought', 'our',
             'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should',
             "shouldn't", 'so', 'some',
             'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
             "there's", 'these', 'they',
             "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
             'very', 'was', "wasn't",
             'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where',
             "where's", 'which', 'while',
             'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll",
             "you're", "you've", 'your',
             'yours', 'yourself', 'yourselves'}


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
    allowed_domains = {
        "ics.uci.edu",
        "cs.uci.edu",
        "informatics.uci.edu",
        "stat.uci.edu",
        "today.uci.edu"
    }

    trap_urls = {
        "?share=",
        "pdf",
        "redirect",
        "#comment",
        "#comments"
        "#respond"
    }

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if parsed.netloc not in allowed_domains:
            return False
        for trap in trap_urls:
            if trap in url:
                return False
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        date_pattern = re.search(r"(\d{4}-\d{2})(?:-\d{2})?", parsed.query)

        if date_pattern:
            date_str = date_pattern.group(1)
            url_date = datetime.strptime(date_str, "%Y-%m")

            if url_date < datetime(2024, 10, 1):
                return False
        
        return True

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
    # print(soup.get_text(separator=" ", strip=True))
