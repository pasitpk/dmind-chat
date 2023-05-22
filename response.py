import openai
from prompts import get_prompt, get_edited_prompt
import time


ref_keys = {'Understanding of Question', 'Understanding of Answer', 'Reason', 'Interpretation Result'}
model = "gpt-3.5-turbo"
max_try = 5
temperature = 0
top_p = 0.05


def gpt_request(model, message):
    messages = [{"role": "user", "content": message}]    
    chat = openai.ChatCompletion.create(
            model=model, 
            messages=messages,
            temperature=temperature,
            top_p=top_p
        )
    reply = chat.choices[0].message.content
    return reply


def request_response(question, text):
    try_count = max_try
    output = None
    while try_count > 0:
        try_count-=1
        try:
            message = get_prompt(question, text)
            output = gpt_request(model, message)
            break
        except Exception as e:
            print('API Error')
            print(e)
            time.sleep(5)

    if output is None:
        return None
    
    try_count = max_try
    while try_count > 0:
        try_count-=1
        try:            
            output = output.replace("'s "," ")
            eval_result = eval(output)     
            text_keys = set(eval_result.keys())
            assert text_keys == ref_keys
            break
        except Exception as e:
            print(e)
            print(output)
            if try_count == 0:
                print('Max tries reached, UNSUCCESSFUL')
                break
            message = get_edited_prompt(question, text, output)
            req_try_count = max_try
            while req_try_count > 0:
                try:
                    output = gpt_request(model,message)
                    break
                except Exception as e:
                    print('API Error')
                    print(e)     
                    time.sleep(5)
                req_try_count -= 1

    if 'yes' in eval_result['Interpretation Result'].lower():
        return 1, eval_result
    return 0, eval_result


class OpenAIResponse:

    def __init__(self, key):
        openai.api_key = key


    def get_response(self, user_states, user_id, text):

        response_text = ""

        if text.lower() == "<end>":        
            response_text = "ขอบคุณที่มาคุยกันนะ"
            if user_id in user_states:
                del user_states[user_id]
            
        if text.lower() == "<2q+>":
            user_states[user_id] = self.get_questions("2q+")
            response_text = user_states[user_id]['questions'].pop(0)
            user_states[user_id]['latest_question'] = response_text

        if text.lower() == "<2q+_extra>":
            user_states[user_id] = self.get_questions("2q+_extra")
            response_text = user_states[user_id]['questions'].pop(0)
            user_states[user_id]['latest_question'] = response_text

        if len(response_text) == 0:
            
            if user_id not in user_states:
                return 'สวัสดีจ้า ฉันคือผู้ช่วยประเมินอาการซึมเศร้า หากคุณต้องการรับการประเมินก็กดปุ่มที่เมนูได้เลยนะ'
            
            qs_form = user_states[user_id]['qs_form']
            question = user_states[user_id]['latest_question']

            score, reason = self.get_score(qs_form, question, text)
            
            if score is None:
                return "ขออภัย ระบบขัดข้อง กรุณาตอบใหม่อีกครั้ง"
            
            user_states[user_id]['scores'].append(score)
            user_states[user_id]['reasons'].append(reason)

            if len(user_states[user_id]['questions']) > 0:
                response_text = user_states[user_id]['questions'].pop(0)
                user_states[user_id]['latest_question'] = response_text

            else:
                response_text = self.get_final_response(qs_form, user_states[user_id])
                del user_states[user_id]

        return response_text
    
    def get_questions(self, qs_form):
        if qs_form.lower() == '2q+':
            return {
                'qs_form': '2q+',
                'questions': [
                    'คุณมีความรู้สึกหดหู่ เศร้า หมดหวัง ไม่สบายใจ เซ็ง ทุกข์ใจ ท้อแท้ ซึม หงอย เครียด กังวล ในเรื่องอะไรบ้างไหมคะ',
                    'ในช่วงนี้ คุณรู้สึกเบื่อ ไม่มีแรงจูงใจ ไม่อยากพูด ไม่อยากทำอะไร หรือทำอะไรก็ไม่สนุกเพลิดเพลินเหมือนเดิมบ้างไหม พอจะเล่าให้ฟังได้ไหมคะ',
                    'ในช่วงหนึ่งเดือนที่ผ่านมานี้ คุณมีความคิดที่ไม่อยากจะมีชีวิตอยู่ต่อไป หรือ บางครั้งเคยมีความคิดอยากตายขึ้นมา หรือ พยายามทำให้ตัวเองจากไปไหมคะ'
                    ],
                'scores': [],
                'reasons': [],
                'latest_question': None
            }
        if qs_form.lower() == '2q+_extra':
            return {
                'qs_form': '2q+_extra',
                'questions': [
                    'คุณมีความรู้สึกหดหู่ เศร้า หมดหวัง ไม่สบายใจ เซ็ง ทุกข์ใจ ท้อแท้ ซึม หงอย เครียด กังวล ในเรื่องอะไรบ้างไหมคะ',
                    'ในช่วงนี้ คุณรู้สึกเบื่อ ไม่มีแรงจูงใจ ไม่อยากพูด ไม่อยากทำอะไร หรือทำอะไรก็ไม่สนุกเพลิดเพลินเหมือนเดิมบ้างไหม พอจะเล่าให้ฟังได้ไหมคะ',
                    'ในช่วงหนึ่งเดือนที่ผ่านมานี้ คุณมีความคิดที่ไม่อยากจะมีชีวิตอยู่ต่อไป หรือ บางครั้งเคยมีความคิดอยากตายขึ้นมา หรือ พยายามทำให้ตัวเองจากไปไหมคะ'
                    ],
                'scores': [],
                'reasons': [],
                'latest_question': None
            }
    
    def get_score(self, qs_form, question, text):
        return request_response(question, text)
    
    def get_final_response(self, qs_form, user_states):

        scores = user_states['scores']
        reasons = user_states['reasons']

        if qs_form.lower() == '2q+':
            return f"""
สรุปคะแนน 2Q+

1. ไม่สบายใจ เซ็ง ทุกข์ใจ เศร้า ท้อแท้ ซึม หงอย : {scores[0]}

2. เบื่อ ไม่อยากพูดไม่อยากทำอะไร หรือทำอะไรก็ไม่สนุกเพลิดเพลินเหมือนเดิม : {scores[1]}

3. มีความรู้สึกทุกข์ใจจนไม่อยากมีชีวิตอยู่ : {scores[2]}

รวมคะแนน : {sum(scores)}
"""   
        
        if qs_form.lower() == '2q+_extra':
            return f"""
สรุปคะแนน 2Q+

1. ไม่สบายใจ เซ็ง ทุกข์ใจ เศร้า ท้อแท้ ซึม หงอย : {scores[0]}
    
    Question : {reasons[0]['Understanding of Question']}

    Answer : {reasons[0]['Understanding of Answer']}

    Reason : {reasons[0]['Reason']}


2. เบื่อ ไม่อยากพูดไม่อยากทำอะไร หรือทำอะไรก็ไม่สนุกเพลิดเพลินเหมือนเดิม : {scores[1]}

    Question : {reasons[1]['Understanding of Question']}

    Answer : {reasons[1]['Understanding of Answer']}

    Reason : {reasons[1]['Reason']}

    
3. มีความรู้สึกทุกข์ใจจนไม่อยากมีชีวิตอยู่ : {scores[2]}

    Question : {reasons[2]['Understanding of Question']}

    Answer : {reasons[2]['Understanding of Answer']}

    Reason : {reasons[2]['Reason']}

    
รวมคะแนน : {sum(scores)}
"""   