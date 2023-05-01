import os

from dotenv import load_dotenv

from flask import Flask, request, abort

from pathlib import Path

import gspread
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

app = Flask(__name__)

# Google Sheets認証情報のファイルパスを指定
# path to 'credentials'/ 'canvas-victor-385302-f1fcd4a95857.json'
credential_path = Path(__file__).parent / 'credentials' / 'canvas-victor-385302-077e5467debb.json'
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', ]

# Google Sheetsへの接続を確立
credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scope)
gc = gspread.authorize(credentials)
gs = gc.open('new_gs_book')
worksheet = gs.sheet1

# LINE Developersのコンソールで取得した値に置き換えてください
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_name = ''
    user_phone = ''

    # ユーザーの名前を尋ねる
    if worksheet.cell(user_id, 2).value == '':
        user_name = event.message.text
        worksheet.update_cell(user_id, 2, user_name)

        # 電話番号を尋ねるメッセージを送信
        reply_text = '名前が記録されました。電話番号を入力してください。'

    # ユーザーの電話番号を尋ねる
    elif worksheet.cell(user_id, 3).value == '':
        user_phone = event.message.text
        worksheet.update_cell(user_id, 3, user_phone)
        reply_text = '電話番号が記録されました。'

    # ユーザーIDが未登録の場合は、ユーザーIDを登録する
    elif worksheet.cell(user_id, 1).value == '':
        worksheet.update_cell(user_id, 1, user_id)
        reply_text = 'ユーザーIDが記録されました。名前を入力してください。'

    # すべての情報が記録されている場合は、完了メッセージを送信する
    else:
        reply_text = '情報がすべて記録されました。'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text))


if __name__ == "__main__":
    app.run()
