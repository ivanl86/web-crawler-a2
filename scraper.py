from datetime import datetime
import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup, Comment
from crawler.database import Database as db

lower_bound = 2500

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

    # Skip page if it's an invalid URL
    if resp.status >= 400 or resp.status == 204 or url in db.invalid_urls:
        db.invalid_urls.add(url)
        return list()
    
    # Skip page if it's empty
    if not resp.raw_response or not resp.raw_response.content:
        db.invalid_urls.add(url)
        return list()
    
    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    # Remove HTML comments
    for comment in soup(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove HTML tags
    web_text = soup.get_text(separator=" ", strip=True)
    # Replace multiple spaces with a single space
    space_delimited_text = re.sub(r"\s+", " ", web_text)
    # Normalize text
    normalized_text = re.sub(r"\s+([?.!])", r"\1", space_delimited_text)

    # Skip page if the text is too short
    if len(normalized_text) < lower_bound:
        db.invalid_urls.add(url)
        return list()
    
    # Tokenize text and save to database
    db.tokenize(url, normalized_text)

    clean_links = set()

    # Extract links and remove fragments
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            parsed_link = urlparse(href)
            link_with_no_frag = urlunparse(
                (parsed_link.scheme, parsed_link.netloc, parsed_link.path, parsed_link.params, parsed_link.query, "")
            )
            clean_links.add(link_with_no_frag)

    return list(clean_links)


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    allowed_domains = {
        "ics.uci.edu",
        "cs.uci.edu",
        "informatics.uci.edu",
        "stat.uci.edu",
        "today.uci.edu/department/information_computer_sciences"
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
        if url in db.invalid_urls:
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
        
        db.unique_urls.add(url)
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
