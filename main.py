import json
import time
from typing import List, Optional
from fastapi import HTTPException, Header, Request, FastAPI
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, AudioMessage, MessageEvent, TextSendMessage
from pydantic import BaseModel
from response import OpenAIResponse
from asr import ASRPipe

with open('config.json', 'r') as f:
    config = json.load(f)

line_bot_api = LineBotApi(config['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(config['LINE_CHANNEL_SECRET'])
asr_pipe_path = config['ASR_PIPE']

asr_pipe = ASRPipe(asr_pipe_path)

openai_response = OpenAIResponse(config['OPENAI_KEY'])

app = FastAPI()

user_states = dict()

class Line(BaseModel):
    destination: str
    events: List[Optional[None]]


@app.get("/")
async def root():
    return {"message": "Hello, DMIND"}


@app.post("/linehook")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="chatbot handle body error.")
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    user_id = event.source.user_id
    text = event.message.text
    timestamp = event.timestamp

    if user_id in user_states:
        
        # ignore requests when processing
        if timestamp < user_states[user_id]['latest_response_timestamp']:
            return        
        
        line_bot_api.push_message(user_id, TextSendMessage(text='กรุณารอสักครู่ ระบบกำลังประมวลผล ...'))
        

    response_text = openai_response.get_response(user_states, user_id, text)

    line_bot_api.push_message(
            user_id, TextSendMessage(text=response_text)
        )
    
    if user_id in user_states:
        user_states[user_id]['latest_response_timestamp'] = time.time() * 1000


@handler.add(MessageEvent, message=AudioMessage)
def message_audio(event):

    user_id = event.source.user_id
    timestamp = event.timestamp

    if user_id in user_states:

        # ignore requests when processing
        if timestamp < user_states[user_id]['latest_response_timestamp']:
            return
        
        line_bot_api.push_message(user_id, TextSendMessage(text='กรุณารอสักครู่ ระบบกำลังประมวลผล ...'))

    message_content = line_bot_api.get_message_content(event.message.id)
    text = asr_pipe.transcribe(message_content)

    response_text = openai_response.get_response(user_states, user_id, text)

    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=response_text)
    )

    if user_id in user_states:
        user_states[user_id]['latest_response_timestamp'] = time.time() * 1000

