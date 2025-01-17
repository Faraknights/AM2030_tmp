def analyze_sentiment(text):
    return "happy" if "good" in text else "sad"




if __name__ == "__main__":
    import sys
    firstarg=sys.argv[1]
    print(analyze_sentiment(firstarg))