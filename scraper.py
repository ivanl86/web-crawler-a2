from datetime import datetime
import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup, Comment
from crawler.database import Database as db

lower_bound = 2500
year_limit = datetime.now().year

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

    # Skip page if it's already scraped or an invalid URL
    if resp.status != 200 or url in db.visited_urls or url in db.invalid_urls:
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

    db.visited_urls.add(url)
    return list(clean_links)


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    allowed_domains = {
        "ics.uci.edu",
        "cs.uci.edu",
        "informatics.uci.edu",
        "stat.uci.edu"
    }

    specific_domain = "today.uci.edu"
    specific_path = "/department/information_computer_sciences"

    trap_urls = {
        "?share=",
        "pdf",
        "redirect",
        "#comment",
        "#comments",
        "#respond"
    }

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            if not parsed.netloc == specific_domain and not parsed.path.startswith(specific_path):
                return False
        if url in db.invalid_urls or url in db.visited_urls:
            return False
        if any(trap in url for trap in trap_urls):
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
        
        # Find year in pattern yyyy
        year_pattern = re.search(r"(\d{4})", parsed.path)

        if year_pattern and year_pattern.group(1):
            year_str = year_pattern.group(1)
            
            # Remove urls that are older than year limit
            if int(year_str) < year_limit:
                return False
        
        # Find date in pattern yyyy-mm-dd
        date_pattern = re.search(r"(\d{4}-\d{2}-\d{2})?", parsed.query)

        if date_pattern and date_pattern.group(1):
            date_str = date_pattern.group(1)

            # Remove urls that are not from today
            if datetime.strftime(date_str, "%Y-%m-%d") != datetime.today().strftime("%Y-%m-%d"):
                return False

            # Remove urls that are older than 2024-10-01
            # if url_date < datetime(2024, 10, 1):
            #     return False
            
        # Track subdomains within `uci.edu` domain
        if parsed.netloc.endswith("uci.edu"):
            db.subdomains[parsed.netloc] = db.subdomains.get(parsed.netloc, 0) + 1
        
        db.unique_urls.add(url)
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        # raise
        return False
