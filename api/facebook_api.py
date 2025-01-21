import requests

def get_facebook_insights(base_url, page_id, access_token, since, until, metric, period="day"):
    url = f"{base_url}/{page_id}/insights"
    params = {
        "metric": metric,
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
