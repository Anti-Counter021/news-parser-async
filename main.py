import asyncio
import json
import os

import aiofiles
import aiohttp
import bs4

url: str = 'https://hi-tech.news/'

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'
}

results = []


def write_results():
    with open('results.json', 'w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)


async def write_file(file_path: str, file: bytes) -> None:
    """
        Write file
        :param file_path: File path
        :type file_path: str
        :param file: File
        :type file: bytes
        :return: None
    """

    async with aiofiles.open(file_path, 'wb') as buffer:
        await buffer.write(file)


async def download_file(session: aiohttp.ClientSession, url: str) -> None:
    """
        Download file
        :param session: Session
        :type session: ClientSession
        :param url: URL
        :type url: str
        :return: None
    """

    async with session.get(url, headers=headers) as response:
        response.raise_for_status()

        if not os.path.exists('media'):
            os.mkdir('media')

        await write_file(f'media/{url.split("/")[-1]}', await response.read())


async def get_page_data(session: aiohttp.ClientSession, page: int) -> None:
    """
        Get page data
        :param session: Session
        :type session: ClientSession
        :param page: Page
        :type page: int
        :return: None
    """

    _url = url + f'/page/{page}/'

    async with session.get(_url, headers=headers, allow_redirects=True) as response:
        response.raise_for_status()
        response_text = await response.text()

        bs = bs4.BeautifulSoup(response_text, 'lxml')

        posts = bs.select('.post')

        for post in posts:
            try:
                title = post.select_one('.title').text
            except:
                title = 'Not found'

            try:
                link = post.select_one('.post-title-a').get('href')
            except:
                link = 'Not found'

            try:
                image = post.select_one('img').get('src')
                image = url + image
                await download_file(session, image)
                image_path = f'media/{image.split("/")[-1]}'
            except:
                image_path = 'Not found'

            results.append(
                {'title': title, 'link': link, 'image': image_path}
            )


async def gather_data() -> None:
    """
        Gather data
        :return: None
    """

    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()

        bs = bs4.BeautifulSoup(await response.text(), 'lxml')
        last = int(bs.select('.navigations > a')[-1].text)

        tasks = []

        for page in range(1, last + 1):
            task = asyncio.create_task(get_page_data(session, page))
            tasks.append(task)

        await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data())
    write_results()


if __name__ == '__main__':
    main()
