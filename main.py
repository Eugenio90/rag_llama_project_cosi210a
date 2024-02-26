
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os
import streamlit as st
import time
from query_engine import create_query_engine
import pandas as pd


api_key = st.secrets["API_KEY"]
os.environ['OPENAI_API_KEY'] = api_key

# Assuming your setup code works as intended
def load_query_engine():
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    return query_engine

query_engine = create_query_engine()

# Create tabs
llm_text, RuleBook_Tab, SQL_table = st.tabs(["LLM_TEXT", "RuleBook", "SQL_Table"])


# Content for Tab 1
with llm_text:
    st.header("LLM")
    st.title('NBA Rulebook and Database')

    user_query_text = st.text_input("Ask a question about the NBA RuleBook or SQL Database", key="rulebook")

    if user_query_text:
        with st.spinner(text = "In progress"):
            time.sleep(3)
        response = query_engine.query(user_query_text)
        st.subheader("Answer to your question:")
        st.write(response.response)
        # st.text("Data Found")
        # st.write(response.print_response_stream())
        with st.expander("See details"):
            st.write(response.metadata)
            st.json(response)


with RuleBook_Tab:
    # Function to read the content of the text file
    def read_text_file(file_path):
        with open(file_path, 'r', errors='ignore') as file:
            return file.read()
    st.header("NBA RuleBook 2023-2024 File Content")
    file_content = read_text_file('./data/nba_rulebook_2023_24.txt')  # Assuming text.txt is in the same directory as the app
    st.text_area("Here's the content of the RuleBook:", file_content, height=300)
    # https://official.nba.com/wp-content/uploads/sites/4/2023/10/2023-24-NBA-Season-Official-Playing-Rules.pdf
    st.markdown('<a href="https://official.nba.com/wp-content/uploads/sites/4/2023/10/2023-24-NBA-Season-Official-Playing-Rules.pdf" target="_blank"> Click here for Orignial Document at NBA site </a>', unsafe_allow_html=True)

with SQL_table:
    st.header("Tabular Data")
    file_path ="C:/cs/s24/210a/streamlit/nba_stats_clean.csv"
    df = pd.read_csv(file_path)

    st.dataframe(df)



