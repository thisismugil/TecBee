import requests

def test(url):
    print(f"\nTesting {url}")
    try:
        r = requests.get(url, timeout=10)
        print("Status:", r.status_code)
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    test("https://www.google.com")
    test("https://www.linkedin.com")
    test("https://api.linkedin.com/v2/me")
