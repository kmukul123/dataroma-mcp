import requests
from bs4 import BeautifulSoup
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
r = requests.get('https://www.dataroma.com/m/ins/ins.php?sym=META', headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
grid = soup.find('table', {'id': 'grid'})
for row in grid.find('tbody').find_all('tr')[:2]:
    tds = row.find_all('td')
    for i, td in enumerate(tds):
        print(f"Col {i}: {repr(td.text.strip())}")
    print("---")
