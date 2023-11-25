import cv2
import numpy as np
import streamlit as st
import yaml, os, replicate, requests
from matplotlib import pyplot as plt

with open('/Users/1zuu/Desktop/LLM RESEARCH/awesome-llm-projects/cadentials.yaml') as f:
    credentials = yaml.load(f, Loader=yaml.FullLoader)

os.environ['REPLICATE_API_TOKEN'] = credentials['REPLICATE_API_TOKEN']

def llava_inference(
                    image,
                    prompt,
                    max_tokens,
                    temperature,
                    top_p
                    ):
    output = replicate.run(
                            "yorickvp/llava-13b:c293ca6d551ce5e74893ab153c61380f5bcbd80e02d49e08c582de184a8f6c83",
                            input={
                                    "image": image,
                                    "prompt": prompt,
                                    "max_tokens": max_tokens,
                                    "temperature": temperature,
                                    "top_p": top_p
                                    }
                        )
    return output

st.set_page_config(page_title="🦙💬 Talk with LLaVA")

with st.sidebar:
    st.title('🦙💬 Talk with LLaVA')
    temperature = st.sidebar.slider(
                                    'temperature', 
                                    min_value=0.01, 
                                    max_value=5.0, 
                                    value=0.1, 
                                    step=0.01
                                    )
    
    top_p = st.sidebar.slider(
                            'top_p', 
                            min_value=0.01, 
                            max_value=1.0, 
                            value=0.9, 
                            step=0.01
                            )
    
    max_tokens = st.sidebar.slider(
                                'max_tokens', 
                                min_value=64, 
                                max_value=4096, 
                                value=512, 
                                step=8
                                )

uploaded_file = st.file_uploader("Upload an image to talk", type=["jpg", "png", "jpeg"])
if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    opencv_image = cv2.imdecode(file_bytes, 1)

    st.image(opencv_image, channels="BGR")

def generate_llava_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            if dict_message.get("type") == "image":
                string_dialogue += "User: [Image]\\n\\n"
            else:
                string_dialogue += "User: " + dict_message["content"] + "\\n\\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\\n\\n"
    output = llava_inference(
                            uploaded_file,
                            prompt,
                            max_tokens,
                            temperature,
                            top_p
                            )
    return output

# Ensure session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"])
        else:
            st.write(message["content"])

# Sidebar to clear chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Text input for chat
prompt = st.text_input("send me your query:")

# Button to send the message/image
if st.button('Send'):
    if uploaded_file:
        # If an image is uploaded, store it in session_state
        st.session_state.messages.append({"role": "user", "content": uploaded_file, "type": "image"})
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate a new response if the last message is not from the assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = generate_llava_response(prompt)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)