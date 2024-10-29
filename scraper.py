import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup, Comment
from crawler.database import Database as db
from simhash import Simhash

# @TODO Remove after test phase
# import time


lower_bound = 2500
simhash_threshold = 5
# page_limit = 5
space_delim_re = re.compile(r"\s+")
normalize_re = re.compile(r"\s+([?.!])")
date_in_path_re = re.compile(r"(\d{4})(?:[/-](\d{1,2})(?:[/-](\d{1,2}))?)?")
date_in_query_re = re.compile(r"(\d{4})((?:-\d{1,2})?)((?:-\d{1,2})?)?")
# pagination_re = re.compile(r"/page/(\d+)?")
invalid_url_ext_re = re.compile(r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|wma|zip|rar|gz)$", re.IGNORECASE)


def scraper(url, resp):
    links = extract_next_links(url, resp)
    # @TODO Remove after test phase
    # start = time.time()
    valid_links = [link for link in links if is_valid(link)]
    # run_time = time.time() - start
    # print(f"is_valid runtime: {run_time:.4f} seconds")
    return valid_links


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
    space_delim_text = space_delim_re.sub(" ", web_text)
    # Normalize text
    normalized_text = normalize_re.sub(r"\1", space_delim_text)

    # Skip page if it has high similarity to other pages
    sim_hash = Simhash(normalized_text)
    if any(abs(hash - sim_hash.value) <= simhash_threshold for hash in db.content_hash):
        db.content_hash.add(sim_hash.value)
        db.invalid_urls.add(url)
        return list()
    
    db.content_hash.add(sim_hash.value)

    # Skip page if the text is too short
    if len(normalized_text) < lower_bound:
        db.invalid_urls.add(url)
        return list()
    
    # Tokenize text and save to database
    # @TODO Remove after test phase
    # start = time.time()
    db.tokenize(url, normalized_text)
    # run_time = time.time() - start
    # print(f"tokenize runtime: {run_time:.4f} seconds")

    # clean_links = set()

    # for link in soup.find_all('a'):
    #     href = link.get('href')
    #     if href and "filter" not in href:
    #         parsed_link = urlparse(href)
    #         link_with_no_frag = urlunparse(
    #             (parsed_link.scheme, parsed_link.netloc, parsed_link.path, parsed_link.params, parsed_link.query, "")
    #         )
    #         clean_links.add(link_with_no_frag)

    # Extract links and remove fragments
    clean_links = {
        urlunparse(urlparse(href)._replace(fragment=""))  # Remove fragment
        for link in soup.find_all('a')
        if (href := link.get('href'))
    }

    db.visited_urls.add(url)
    return list(clean_links)


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


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)

        if (parsed.scheme not in {"http", "https"} or
            not any(parsed.netloc.endswith(domain) for domain in allowed_domains) and
            not (parsed.netloc == specific_domain or parsed.path.startswith(specific_path)) or
            url in db.invalid_urls or
            url in db.visited_urls or
            any(trap in url for trap in trap_urls) or
            invalid_url_ext_re.match(parsed.path.lower()) or
            "filter" in url or
            # Invalid if a link contains date
            date_in_path_re.search(parsed.path) or
            date_in_query_re.search(parsed.query)):

            db.invalid_urls.add(url)
            return False
        # if parsed.scheme not in set(["http", "https"]):
        #     return False
        # if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
        #     if not parsed.netloc == specific_domain and not parsed.path.startswith(specific_path):
        #         return False
        # if url in db.invalid_urls or url in db.visited_urls:
        #     return False
        # if any(trap in url for trap in trap_urls):
        #     return False
        # if invalid_url_ext_re.match(parsed.path.lower()):
        #     return False
        
        # # Invalid if a link contains date
        # if date_in_path_re.search(parsed.path):
        #     return False
        # if date_in_query_re.search(parsed.query):
        #     return False
        
        # Invalid after page limit
        # pagination_match = pagination_re.search(parsed.path)
        # if pagination_match:
        #     page_num = int(pagination_match.group(1))
        #     if page_num > page_limit:
        #         return False
            
        # Track subdomains within `uci.edu` domain
        if parsed.netloc.endswith("uci.edu"):
            db.subdomains[parsed.netloc] = db.subdomains.get(parsed.netloc, 0) + 1
        
        db.unique_urls.add(url)
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        # raise
        return False
