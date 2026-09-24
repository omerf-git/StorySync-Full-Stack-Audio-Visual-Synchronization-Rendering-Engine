import requests
import json
import os
import concurrent.futures

# Blacklist for domains that typically have heavy watermarks
WATERMARK_BLACKLIST = [
    "gettyimages",
    "shutterstock",
    "istockphoto",
    "alamy",
    "freepik",
    "dreamstime",
    "depositphotos",
    "123rf",
    "pond5",
    "as2.ftcdn",
    "vecteezy",
    "bigstockphoto",
    "as1.ftcdn",
    "stock.adobe.com",
    "media.istockphoto.com",
    "www.gettyimages.com"
]

def check_image_url(img):
    """
    Validates if an image URL is reachable and actually an image.
    Returns the image object if valid, else None.
    """
    url = img.get('imageUrl')
    if not url:
        return None
        
    try:
        # Use HEAD request for speed. Some servers block HEAD, so we fallback or accept it.
        # Timeout is small to avoid long waits
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.head(url, headers=headers, timeout=2.0, allow_redirects=True)
        
        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "")
            if "image" in content_type.lower():
                return img
    except Exception:
        # If HEAD fails or timeouts, we skip it
        return None
        
    return None

def search_images(keyword, api_key=None):
    if not api_key:
        api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise ValueError("Please set the SERPER_API_KEY environment variable.")

    url = "https://google.serper.dev/images" 

    payload = json.dumps({
      "q": keyword,
      "gl": "us",
      "hl": "en",
      "num": 40 # Ask for more results so we have enough after filtering
    })

    headers = {
      'X-API-KEY': api_key,
      'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if "images" in data:
            MIN_WIDTH = 800
            MIN_HEIGHT = 600
            
            # Step 1: Filter resolution and watermark blacklist
            basic_filtered = []
            for img in data['images']:
                w = img.get('imageWidth', 0)
                h = img.get('imageHeight', 0)
                source = img.get('source', '').lower()
                img_url = img.get('imageUrl', '').lower()
                
                is_horizontal = (w >= h)
                is_high_res = (w >= MIN_WIDTH and h >= MIN_HEIGHT)
                
                # Check blacklist
                has_watermark = any(domain in source or domain in img_url for domain in WATERMARK_BLACKLIST)
                
                if is_horizontal and is_high_res and not has_watermark:
                    basic_filtered.append(img)
            
            # We don't want to check 40 URLs, it takes too long even async. Let's cap at 15.
            basic_filtered = basic_filtered[:15]
            
            # Step 2: Validate URLs concurrently
            validated_images = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit all tasks
                future_to_img = {executor.submit(check_image_url, img): img for img in basic_filtered}
                
                for future in concurrent.futures.as_completed(future_to_img):
                    result = future.result()
                    if result is not None:
                        validated_images.append(result)
            
            # Since as_completed yields randomly, we can re-sort them based on original order if we want,
            # but for now returning them in any validated order is fine.
            
            return validated_images
        else:
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during API Request: {e}")
        return []
