import openai
import streamlit as st
import docx
import os
from streamlit_chat import message
from io import StringIO
import base64

# Setting page title and header
st.set_page_config(page_title="AVA", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>Writer. You do the research, I write the paper</h1>", unsafe_allow_html=True)

# Create a left column in the Streamlit interface
left_column = st.sidebar

# Add a title and an input box for the OpenAI API key in the left column
left_column.title("Essay Writer")
api_key = left_column.text_input("Enter your OpenAI API key:", type="password")
openai.api_key = api_key

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

# Upload a DOCX file
uploaded_file = left_column.file_uploader("Upload a DOCX file with quotes from various articles on the topic you are researching, including the reference in APA format (max. 2000 words):", type=["docx"])

# Read and extract citations and references from the uploaded file
def extract_citations(docx_file):
    doc = docx.Document(docx_file)
    citations = []
    references = []
    for paragraph in doc.paragraphs:
        text = paragraph.text
        if text.startswith("Cita:"):
            citations.append(text[6:])
        elif text.startswith("Referencia:"):
            references.append(text[12:])
    return citations, references

if uploaded_file is not None:
    with open("temp.docx", "wb") as f:
        f.write(uploaded_file.getbuffer())
    citations, references = extract_citations("temp.docx")
    os.remove("temp.docx")
else:
    citations = []

# generate a response
def generate_response(prompt):
    if citations:
        st.session_state['messages'].insert(1, {"role": "system", "content": f"Utiliza las siguientes citas relevantes en tu respuesta: {', '.join(citations)}"})
    
    st.session_state['messages'].append({"role": "user", "content": prompt})

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=st.session_state['messages']
    )
    response = completion.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": response})
    
    if citations:
        st.session_state['messages'].pop(1)

    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output, total_tokens, prompt_tokens, completion_tokens = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)

        if citations:
            markdown_text = f"{output}\n\n{''.join([f'- {cite}\n' for cite in citations])}"
            markdown_bytes = StringIO(markdown_text).read().encode("utf-8")
            b64 = base64.b64encode(markdown_bytes).decode()
            href = f"<a href=\"data:file/markdown;base64,{b64}\" download=\"generated_essay.md\">Download generated essay in Markdown format</a>"
            st.markdown(href, unsafe_allow_html=True)

        st.session_state['total_tokens'].append(total_tokens)

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
