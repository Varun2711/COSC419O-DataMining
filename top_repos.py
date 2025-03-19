import requests

def get_top_repos(language, sort='stars', order='desc', per_page=10):
    url = 'https://api.github.com/search/repositories'
    params = {
        'q': f'language:{language}',
        'sort': sort,
        'order': order,
        'per_page': per_page
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['items']
    else:
        return None

def main():
    language = 'python'  # Change this to the desired programming language
    top_repos = get_top_repos(language)
    if top_repos:
        for repo in top_repos:
            print(f"Name: {repo['name']}")
            print(f"Owner: {repo['owner']['login']}")
            print(f"Stars: {repo['stargazers_count']}")
            print(f"URL: {repo['html_url']}")
            print('-' * 40)
    else:
        print("Failed to fetch repositories")

if __name__ == '__main__':
    main()