import openai
import streamlit as st
import docx
import os
from streamlit_chat import message

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
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []

# Sidebar
st.sidebar.title("Sidebar")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are skilled writer. With the quotations provided, you write an academic paper that responds to the user's input title. The essay mus have between 2000 and 2500 words, and must be highly original, in the language of the user. I mut include at least ten quotations, from the document provided."}
    ]
    st.session_state['model_name'] = []
    st.session_state['total_tokens'] = []

# Upload a DOCX file
uploaded_file = left_column.file_uploader("Upload a document with quotes from various articles on the topic you are researching, including the reference in APA format (max. 2000 words)", type=["docx"])

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
    response =     completion.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": response})
    
    if citations:
        st.session_state['messages'].pop(1)

    total_tokens = completion.usage.total_tokens
    return response, total_tokens

# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        with st.spinner("Generating answer..."):
            output, total_tokens = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)
        st.session_state['model_name'].append("GPT-4")
        st.session_state['total_tokens'].append(total_tokens)

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
            st.write(
                f"Model used: {st.session_state['model_name'][i]}; Number of tokens: {st.session_state['total_tokens'][i]}")

    # Download the essay in Markdown format
    if st.button("Download essay as Markdown file"):
        markdown_text = "{}{}{}".format(output, os.linesep * 2, "".join(["- {}{}".format(cite, os.linesep) for cite in citations]))
        with open("essay.md", "w") as f:
            f.write(markdown_text)
        st.download_button("Download essay.md", "essay.md", "text/markdown")
        os.remove("essay.md")

