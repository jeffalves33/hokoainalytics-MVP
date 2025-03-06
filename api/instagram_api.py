import requests
from datetime import datetime, timedelta

def get_instagram_reach(base_url, page_id, access_token, since, until, period="day"):
    url = f"{base_url}/{page_id}/insights"
    params = {
        "metric": 'reach',
        "access_token": access_token,
        "period": period,
        "since": since,
        "until": until
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        values = [item["value"] for item in data["data"][0]["values"]]
        return values
    else:
        print(f"Erro: {response.status_code} - {response.text}")
        return None

def get_instagram_impressions(base_url, page_id, access_token, since, until, period="day"):
    start = since
    end = until

    daily_results = []

    current_date = start
    while current_date < end:
        # Calculate the next day
        next_date = current_date + timedelta(days=1)
        
        # Format dates for API
        since = current_date.strftime("%Y-%m-%d")
        until = next_date.strftime("%Y-%m-%d")
        
        # Prepare URL and parameters
        url = f"{base_url}/{page_id}/insights"
        params = {
            "metric": 'views',
            "metric_type": 'total_value',
            "access_token": access_token,
            "period": "day",
            "since": since,
            "until": until
        }
        
        # Make the request
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Extract total value for the day
            if "data" in data and len(data["data"]) > 0:
                daily_value = data["data"][0]["total_value"]["value"]
                daily_results.append(daily_value)
            else:
                print(f"No data found for {since}")
                daily_results.append({
                    "value": 0,
                    "date": since
                })
        else:
            print(f"Error for {since}: {response.status_code} - {response.text}")
            daily_results.append({
                "value": None,
                "date": since
            })
        
        # Move to next day
        current_date = next_date
    
    return daily_results


def get_instagram_follows(base_url, page_id, access_token):
    url = f"{base_url}/{page_id}"
    params = {
        "fields": 'followers_count',
        "access_token": access_token,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        value = data["followers_count"]
        return value
    else:
        print(f"Erro: {response.status_code} - {response.text}")
        return None