import openai
from rich.panel import Panel
import speech_recognition as sr
from rich.console import Console
from elevenlabs import generate, stream
from faster_whisper import WhisperModel
from io import BytesIO
from time import perf_counter

model = WhisperModel("small.en", device="auto")

console = Console(width=80)

openai.api_key_path = "openai.key"

r = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    r.adjust_for_ambient_noise(source)

msg = lambda role: lambda content: {"role": role, "content": content}
Assistant = msg("assistant")
User = msg("user")
System = msg("system")

history = [System("You work an a customer support call center.\nIf the customer requests a refund, ask for the name of the product,why they are dissatisfied and what their order number is.")]

def add_message(message):
    history.append(message)
    match message["role"]:
        case "assistant":
            console.print(Panel(message["content"], title="[bold]AI", title_align="right", width=40), style="yellow", justify="right")
        case "user":
            console.print(Panel(message["content"], title="[bold]User", title_align="left", width=40), style="blue", justify="left")

while True:

    ### STT ###

    with mic as source:
        print(" ", end="", flush=True)
        audio = r.listen(mic)
        print("\r        ", end="\r")
    
    start = perf_counter()
    print("󰔊 ", end="", flush=True)
    segments, info = model.transcribe(BytesIO(audio.get_wav_data()))

    # decode output
    
    text = "".join([s.text for s in segments])
    print("\r        ", end="\r")
    print(f"STT done in {(perf_counter() - start) * 1000:.1f} ms")

    ### GPT ###

    add_message(User(text))
    continue

    print(" ", end="", flush=True)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=128,
        messages=history,
        stream=True
    )
    print("\r        ", end="\r")

    message = ""

    def yield_completion(completion):
        global message
        for chunk in completion:
            #print(chunk)
            try:
                yield chunk.choices[0].delta.content
                message += chunk.choices[0].delta.content
            except:
                continue

    print("󰓃 ", end="", flush=True)
    audio = generate(
        text=yield_completion(completion),
        api_key="9630b36e1fac9868ed208183dd439617", #! fix security
        voice="Liam",
        model="eleven_monolingual_v1", # monolingual_v1 is faster than multilingual_v2,
        stream=True
    )
    stream(audio)
    add_message(Assistant(message))
    print("\r           ", end="\r")