'''
定时自定义
15 7 * * * zaobao60s.py
new Env('融科早报60s');
'''


import requests
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from bs4 import BeautifulSoup
import os
import time
import jieba
from lunar_python import Lunar
import base64
import hashlib

# 企业微信机器人 Webhook URL
webhook_url = os.environ.get('Webhook_URL')  # 替换为你的Webhook URL

def send_image_to_wechat(image_path, webhook_url):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    image_md5 = hashlib.md5(image_data).hexdigest()
    data = {
        "msgtype": "image",
        "image": {
            "base64": image_base64,
            "md5": image_md5
        }
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 200 and response.json().get("errcode") == 0:
        print("图片发送成功")
    else:
        print("图片发送失败:", response.text)

def split_text(text, font, max_width):
    lines = []
    words = jieba.cut(text)
    line = ""
    for word in words:
        test_line = line + word
        text_width, _ = font.getbbox(test_line)[2:4]
        if text_width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def get_run_count():
    count_file = "run_count.txt"
    if os.path.exists(count_file):
        with open(count_file, "r") as file:
            count = int(file.read().strip())
    else:
        count = 0
    count += 1
    with open(count_file, "w") as file:
        file.write(str(count))
    return count

def draw_rectangle_with_shadow(img, x, y, width, height, shadow_offset=10, shadow_color=(0, 0, 0, 100), fill_color=(255, 255, 255, 255)):
    shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle(
        [x + shadow_offset, y + shadow_offset, x + width + shadow_offset, y + height + shadow_offset],
        fill=shadow_color
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img_with_shadow = Image.alpha_composite(img.convert('RGBA'), shadow)
    rect_draw = ImageDraw.Draw(img_with_shadow)
    rect_draw.rectangle(
        [x, y, x + width, y + height],
        fill=fill_color
    )
    return img_with_shadow

def get_lunar_date(date):
    d = Lunar.fromDate(date)
    fest_date = d.getFestivals()[:1]
    festi_date = " ".join(fest_date)
    lunar_date = d.getMonthInChinese() + "月" + d.getDayInChinese() + " " + festi_date
    return lunar_date

def trim_text_to_fit(text, max_chars):
    if len(text) > max_chars:
        return text[:max_chars - 3] + "..."
    return text

def reduce_image_color_depth(image, max_size=2 * 1024 * 1024, initial_bits=8):
    """
    降低 PNG 图片的颜色深度，直到图片大小小于指定的最大大小
    Args:
        image (PIL.Image): 原始图片对象
        max_size (int): 目标最大大小（字节），默认为2MB
        initial_bits (int): 初始颜色深度（位），默认为8位
    Returns:
        str: 调整后的图片路径
    """
    output_stream = BytesIO()
    image.save(output_stream, format='PNG')
    size_in_bytes = output_stream.tell()
    today_date = datetime.now()
    run_count = get_run_count()

    if size_in_bytes <= max_size:
        # 如果当前图片大小已经小于 max_size，直接保存
        output_filename = f"{today_date.strftime('%Y-%m-%d')}_{run_count}_optimized.png"
        image.save(output_filename, format='PNG')
        return output_filename

    # 循环降低颜色深度，直到图片大小符合要求
    for bits in range(initial_bits, 0, -1):
        img_reduced = image.convert('P', palette=Image.ADAPTIVE, colors=2 ** bits)
        output_stream = BytesIO()
        img_reduced.save(output_stream, format='PNG')
        size_in_bytes = output_stream.tell()

        if size_in_bytes <= max_size:
            output_filename = f"{today_date.strftime('%Y-%m-%d')}_{run_count}_reduced_{bits}bit.png"
            img_reduced.save(output_filename, format='PNG')
            return output_filename

    # 如果最低颜色深度仍不满足条件，则保存最后一次尝试
    output_filename = f"{today_date.strftime('%Y-%m-%d')}_{run_count}_reduced_{bits}bit.png"
    img_reduced.save(output_filename, format='PNG')
    return output_filename
"""
def check_and_execute():
    url = "https://60s.viki.moe/60s?v2=1"
    response = requests.get(url)
    data = response.json()
    updated = data['data']['updated']
    news_list = data['data']['news'][:10]
    updated_date = datetime.fromtimestamp(updated / 1000.0)
    today_date = datetime.now()
"""
def check_and_execute():
    url = "https://api.03c3.cn/api/zb?type=jsonText"
    response = requests.get(url)
    data = response.json()
    #updated = data['data']['updated']
    news_list = data['data']['text'][:9]
    urlimg = "https://api.03c3.cn/api/zb?type=jsonImg"
    response = requests.get(urlimg)
    data = response.json()
    updated = data['data']['datetime']
    updated_date = datetime.strptime(updated, "%Y-%m-%d")
    #updated_date = datetime.fromtimestamp(updated / 1000.0)
    today_date = datetime.now()



    if updated_date.date() == today_date.date():
        img_page_url = "https://bz.w3h5.com/img/rand_m"
        img_page_response = requests.get(img_page_url)
        
        if img_page_response.status_code == 200:
            soup = BeautifulSoup(img_page_response.content, 'html.parser')
            img_tag = soup.find('img')
            img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
        else:
            img_url = None

        if img_url:
            img_response = requests.get(img_url)
            img = Image.open(BytesIO(img_response.content)) if img_response.status_code == 200 else Image.open("local_test_image.jpg")
        else:
            img = Image.open("local_test_image.jpg")

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 130))
        img_with_overlay = Image.alpha_composite(img.convert('RGBA'), overlay)

        margin = 70
        rect_width = img.width - 2 * margin
        rect_height = 450
        rect_x = margin
        rect_y = margin
        img_with_rectangle = draw_rectangle_with_shadow(img_with_overlay, rect_x, rect_y, rect_width, rect_height)

        border_margin = 40
        border_width = 5
        border_color = (255, 255, 255, 153)

        draw = ImageDraw.Draw(img_with_rectangle)
        for i in range(border_width):
            draw.rectangle(
                [border_margin - i, border_margin - i, img.size[0] - border_margin + i, img.size[1] - border_margin + i],
                outline=border_color
            )

        lun_date = Lunar.fromDate(updated_date)
        yi = lun_date.getDayYi()
        ji = lun_date.getDayJi()
        yi_text = "宜：" + ",".join(yi)
        ji_text = "忌：" + ",".join(ji)
        max_chars_per_line = 34
        yi_text_trimmed = trim_text_to_fit(yi_text, max_chars_per_line)
        ji_text_trimmed = trim_text_to_fit(ji_text, max_chars_per_line)

        font_path = "OPlusSans3-Bold.ttf"
        font_size = 34
        font = ImageFont.truetype(font_path, font_size)

        text_position = (70, 580)
        text_color = (255, 255, 255)
        line_spacing = 10
        max_width = rect_width
        #numbered_news_list = [f"{idx + 1}、{news}" for idx, news in enumerate(news_list)]

        y_offset = text_position[1]
        for news in news_list:
            news_lines = split_text(news, font, max_width)
            for line in news_lines:
                draw.text((text_position[0], y_offset), line, font=font, fill=text_color)
                y_offset += font.getbbox(line)[3] + line_spacing
            y_offset += 20

        date_text = updated_date.strftime("今天是%Y年%m月%d日")
        day_of_week = updated_date.strftime("%A")
        day_of_week_cn = {
            'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三',
            'Thursday': '星期四', 'Friday': '星期五', 'Saturday': '星期六',
            'Sunday': '星期天'
        }.get(day_of_week, day_of_week)
        date_text += " " + day_of_week_cn
        lunar_date_text = date_text + "  农历" + get_lunar_date(updated_date)

        rske_font_size = 220
        #rske_color = (9, 188, 210)
        rske_color = (0,207,231)
        rske_font = ImageFont.truetype(font_path, rske_font_size)
        rske_text_position = (rect_x + 20, rect_y - 10)
        rske_text = "融科早报"

        date_font_size = 33
        itm_color = (0, 0, 0)
        date_font = ImageFont.truetype(font_path, date_font_size)
        date_text_position = (rect_x + 25, rect_y + 270)
        lunar_date_text_position = (rect_x + 25, rect_y + 290)
        draw.text(rske_text_position, rske_text, font=rske_font, fill=rske_color)
        #draw.text(date_text_position, date_text, font=date_font, fill=itm_color)
        draw.text(lunar_date_text_position, lunar_date_text, font=date_font, fill=itm_color)
        draw.text((95, 410), yi_text_trimmed, font=date_font, fill=itm_color)
        draw.text((95, 460), ji_text_trimmed, font=date_font, fill=itm_color)

        run_count = get_run_count()
        output_filename = f"{today_date.strftime('%Y-%m-%d')}_{run_count}.png"
        img_with_rectangle.convert('RGB').save(output_filename)
        if os.path.getsize(output_filename) > 2 * 1024 * 1024:
            output_filename = reduce_image_color_depth(img_with_rectangle)
        print(f"新闻已更新，生成的图片保存为: {output_filename}")
        
        # 发送图片到企业微信机器人
        send_image_to_wechat(output_filename, webhook_url)
        exit(0)
    else:
        print("新闻未更新")

while True:
    check_and_execute()
    print("等待10分钟后再次检查...")
    time.sleep(600)  # 10分钟后再次检查
