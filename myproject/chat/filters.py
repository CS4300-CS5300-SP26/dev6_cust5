BANNED_WORDS = [
    'Baby Seal',
    'Club',
    # add more here
]

#Function to replace the banned words with 0's
def filter_message(content):
    for word in BANNED_WORDS:
        content = content.replace(word, '0' * len(word))
    return content