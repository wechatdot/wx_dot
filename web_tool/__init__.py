import requests
import os
from urllib.parse import urlparse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

count = 0

# default_proxy = "http://192.168.2.2:7890"
default_proxy = ""

def download_image(url, save_dir, from_id, proxy_url=default_proxy):
    if proxy_url:
        proxies = {'http': proxy_url, 'https': proxy_url}
        response = requests.get(url, headers=headers, proxies = proxies)
    else:
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content_type = response.headers.get('content-type')
        if content_type.startswith('image'):
            # 获取文件扩展名
            extension = '.' + content_type.split('/')[-1]

            # 获取文件名
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            file_name = os.path.splitext(file_name)[0]

            # 拼接保存文件的路径
            global count
            save_path = os.path.join(save_dir, from_id + "_" + str(count) +file_name + extension)
            count += 1

            # 保存图片文件
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print('图片下载完成！保存路径:', save_path)
            return save_path
        else:
            print('URL不是图片！')
            return ""
    else:
        print('图片下载失败！')
        return ""


def download_file(url, save_dir, from_id ="", proxy_url=default_proxy):
    if proxy_url:
        proxies = {'http': proxy_url, 'https': proxy_url}
        response = requests.get(url, stream=True, headers=headers, proxies = proxies)
    else:
        response = requests.get(url, stream=True, headers=headers)

    if response.status_code == 200:
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"\'')
        else:

            filename = url.split('/')[-1]
        global count
        filepath = os.path.join(save_dir, from_id + "_" + str(count) + filename)
        count += 1

        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f'文件已下载并保存为: {filepath}')
        return filepath
    else:
        print('请求失败，无法下载文件。')
        return ""


