import json
from random_words import RandomWords
import random
from datetime import datetime


def generate_random_urls(word, url_word):
    '''Generate random urls for a word
    For any word, pick a random number of urls to return 
    and choose random urls starting with the second letter of the word
    '''
    rw = RandomWords()
    r = random.randint(2,6)
    words = rw.random_words(count=r, letter=word[0])
    urls = []
    for word in words:
        url = "https://www."+word+url_word+".com"
        urls.append(url)
    if word == 'close':
        print(urls)
    return urls

def generate_indices(status='committed', url_word='', lower_range=1, upper_range=50):
    import os
    file_path = os.path.join(os.path.dirname(__file__), 'synonyms.txt')
    f = open(file_path, 'rb')
    
    indices = {}
    linecount = 0
    for line in f:
        words = line.decode('utf-8').strip().split(",")
        for i in range(len(words)):
            words[i] = words[i].strip()
        linecount += 1
        # pick only first sets in lines [lower_range, upper range]
        if linecount < lower_range:
            continue
        if linecount > upper_range:
            break
        for word in words:
            word = word.strip()
            if len(word) == 0:
                continue
            indices[word] = {}
            indices[word]['status'] = status
            indices[word]['sim_words'] = words
            indices[word]['urls'] = generate_random_urls(word, url_word)
        json_list = []

        for word in indices:
            indices[word]['name'] = word
            json_list.append(indices[word])
    return json_list

def main():
    # indices = generate_indices()
    json_list = []

    # for word in indices:
    #   indices[word]['name'] = word
    #   json_list.append(indices[word])

    #with open('indices.json', 'w') as fp:
    #   json.dump(json_list, fp, sort_keys=True, indent=4)

if __name__ == '__main__':
    main()