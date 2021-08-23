import json

def main():
    with open("original_lbs.json", "r") as f:
        original_lbs = json.load(f)

    output = ""

    for lb in original_lbs["leaderboards"]:
        
    print(
    
if __name__ == "__main__":
    main()
