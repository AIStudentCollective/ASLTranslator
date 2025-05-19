import google.generativeai as genai
import time
# uv pip install -q -U google-generativeai

GOOGLE_API_KEY = "AIzaSyAOwGWeeFcrcsj6Fqon1V6IqjPbs7DcxDU"

#

genai.configure(api_key=GOOGLE_API_KEY)

# video_file_name = "Greetings/48. Hello/MVI_0029.MOV"

video_file_name = "Greetings/49. How are you/MVI_9921.MOV"


print(f"Uploading file...")
video_file = genai.upload_file(path=video_file_name)
print(f"Completed upload: {video_file.uri}")



# Check whether the file is ready to be used.
while video_file.state.name == "PROCESSING":
    print('.', end='')
    time.sleep(10)
    video_file = genai.get_file(video_file.name)

if video_file.state.name == "FAILED":
  raise ValueError(video_file.state.name)


# Create the prompt.
prompt = "the person in the video is doing Indian sign language. What are they signing? Output that in english text. "

# Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

# Make the LLM request.
print("Making LLM inference request...")
response = model.generate_content([video_file, prompt],
                                  request_options={"timeout": 600})


print(response.text)