import re
import requests
import time
import argparse
from datetime import datetime

candidate_list = ['unified/x86_64/', 'cpu/x86_64/', 'cpu/aarch64/']

def gen_url(path):
    max_try_time = 5
    current_year_month = datetime.now().strftime("%Y%m")
    current_year_month_day = datetime.now().strftime("%Y%m%d")
    url_prefix = f'http://repo.mindspore.cn/mindspore/mindspore/version/{current_year_month}/{current_year_month_day}'
    
    content = requests.get(url_prefix)
    master_links = re.findall(r'href=["\'](.*?master.*?)["\']', content.text)

    if not master_links:
        raise ValueError('Today not found master whl package.')

    url_prefix = url_prefix + f'/{master_links[-1]}'
    print(url_prefix)
    
    retry_count = {}
    for url_suffix in candidate_list:
        url = url_prefix + url_suffix
        response = requests.get(url)

        html = response.text

        pattern = re.compile(r'<a href="mindspore-(.*?).whl"')
        matches = re.findall(pattern, html)

        while matches:
            match = matches.pop(0)
            if '39' not in match:
                continue
            if match not in retry_count:
                retry_count[match] = 0
            
            if retry_count[match] > max_try_time:
                raise ValueError('max retry time.')
            whl_name = 'mindspore-' + match + '.whl'
            idx = match.index('cp')
            save_name = 'mindspore-newest-' + match[idx:] + '.whl'

            whl_url = url + whl_name
            print(whl_url)
            # # 使用 stream=True 发送 GET 请求
            response = requests.get(whl_url, stream=True)

            # 打开本地文件，以二进制写入模式
            print('Start download：', whl_name)
            try:
                with open(path + save_name, 'wb') as f:
                    # 循环读取响应内容的每个数据块，然后写入本地文件
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print('Download：', save_name)
            except Exception as e:
                print(e)
                print('Resume', match)
                matches.append(match)
                retry_count[match] += 1
                time.sleep(5) # sleep for next retry



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str)
    args = parser.parse_args()

    gen_url(args.path)
