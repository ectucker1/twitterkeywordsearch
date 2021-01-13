# Generate the Twitter query for a specified file
def load_query(query_path):
    # Create a list of the key phrases
    keys = []
    # Open the file and read each line
    with open(query_path, 'r') as file:
        for line in file:
            parsed = line.strip()
            # Verify that the line is not empty
            if len(parsed) > 0:
                # Add that line to the list of keywords
                keys.append(parsed)

    # If there are too many keywords, throw an error
    # See limit specified at https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/guides/standard-operators
    if len(keys) > 10:
        raise Exception("Search is too complex, limit to 10 keykeys")

    # Join keywords together, surrounded by quotes and OR operators
    query = ""
    for i, word in enumerate(keys):
        query += f'"{word}" '
        if i < len(keys) - 1:
            query += 'OR '

    # Return the generated query
    return query
