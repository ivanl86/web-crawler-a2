import re
from collections import Counter

class Database:
    invalid_urls = set()
    # Save all unique urls for problem 1
    unique_urls = set()
    # Save longest page url and its word count for problem 2
    longest_page = ["", 0]
    # Save all tokens and their occurence for problem 3
    tokens = dict()
    # Save all subdomains and their unique urls for problem 4
    subdomains = dict()
    
    @staticmethod
    def write_unique_urls():
        with open("unique_urls.txt", "w") as f:
            f.write(f"Total unique urls found: {len(Database.unique_urls)}\n")
            f.writelines(f"{url}\n" for url in Database.unique_urls)

    @staticmethod
    def write_longest_page():
        with open("longest_page.txt", "w") as f:
            f.write(f"{Database.longest_page[0]} {Database.longest_page[1]}\n")

    @staticmethod
    def write_common_tokens():
        top_common_words = sorted(((token, count) for token, count in Database.tokens.items() if token not in stop_words), key=lambda item: item[1], reverse=True)[:50]
        with open("tokens.txt", "w") as f:
            f.writelines(f"{token} {count}\n" for token, count in top_common_words)

    @staticmethod
    def write_subdomains():
        with open("subdomains.txt", "w") as f:
            f.writelines(f"{subdomain}\n" for subdomain in sorted(Database.subdomains.items()))

    @staticmethod
    def tokenize(url, text):
        tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())

        # Find the longest page including stop words in problem 2
        token_count = len(tokens)
        if token_count > Database.longest_page[1]:
            Database.longest_page = [url, token_count]

        token_dict = Counter(tokens)
        
        # Save and count the occurence of each token in problem 3
        for token, count in token_dict.items():
            Database.tokens[token] = Database.tokens.get(token, 0) + count


# A set of stop words that will be ignored when finding the most common words in problem 3
stop_words = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as',
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
    'yours', 'yourself', 'yourselves'
}
