import hashlib
all_tags = {"corona": 0, "economy": 1, "job": 2, "china": 3, "election": 4, "race": 5}


def convert_tags_to_int(tags):
    int_value = 0
    for tag in tags:
        int_value += 2 ** all_tags.get(tag)
    return int_value


def convert_int_to_tags(int_value):
    tags = []
    for num in range(len(all_tags)):
        if (2 ** num) & int_value:
            tags.append(list(all_tags.keys())[num])
    return tags


def tweet_hash_key(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()
