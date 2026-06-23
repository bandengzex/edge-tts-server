from flask import Flask, request, Response, jsonify
import edge_tts
import asyncio

app = Flask(__name__)

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

def speed_to_rate(speed):
    try:
        speed = float(speed)
        rate = int((speed - 5) * 10)
        return f"+{rate}%" if rate >= 0 else f"{rate}%"
    except:
        return "+0%"

async def generate_audio(text, voice, rate, volume):
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"service": "edge-tts-http", "status": "ok"})

@app.route('/voices', methods=['GET'])
def voices():
    try:
        voices_list = asyncio.run(edge_tts.list_voices())
        zh_voices = [v for v in voices_list if v['Locale'].startswith('zh')]
        return jsonify({"total": len(voices_list), "chinese": zh_voices})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tts', methods=['GET', 'POST'])
def tts():
    if request.method == 'GET':
        text = request.args.get('text', '')
        voice = request.args.get('voice', DEFAULT_VOICE)
        rate = request.args.get('rate', '+0%')
        volume = request.args.get('volume', '+0%')
        spd = request.args.get('spd', None)
        per = request.args.get('per', None)
    else:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        text = data.get('text', '') or data.get('tex', '')
        voice = data.get('voice', DEFAULT_VOICE) or data.get('per', DEFAULT_VOICE)
        rate = data.get('rate', '+0%')
        volume = data.get('volume', '+0%')
        spd = data.get('spd', None)
        per = data.get('per', None)
    
    if per and per != DEFAULT_VOICE:
        voice = per
    if spd:
        rate = speed_to_rate(spd)
    
    if not text:
        return jsonify({"error": "text 参数不能为空"}), 400
    
    try:
        audio_data = asyncio.run(generate_audio(text, voice, rate, volume))
        return Response(
            audio_data,
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=tts.mp3",
                "Content-Length": str(len(audio_data))
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "Edge TTS HTTP Server",
        "version": "1.0",
        "default_voice": DEFAULT_VOICE
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
