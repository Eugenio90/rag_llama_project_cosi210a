import os
import llama_index
import openai
import pandas as pd
import logging
import sys
import nest_asyncio
import streamlit as st
# pinecone
from pinecone import Pinecone, ServerlessSpec

# LLama_Index 
from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine import SQLAutoVectorQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import SQLDatabase


from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    select,
    column,
    DateTime,
)

from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector


def create_query_engine():
    api_key = st.secrets["API_KEY"]
    os.environ['OPENAI_API_KEY'] = api_key
    file_path ="C:/cs/s24/210a/streamlit/nba_stats_clean.csv"
    df = pd.read_csv(file_path, index_col=0)

    engine = create_engine("sqlite://")
    # engine = create_engine("sqlite:///:memory:")
    metadata_obj = MetaData()
    # Define the game_stats table
    game_stats_table = Table(
        "game_stats",  # Table name
        metadata_obj,
        Column("date", String(32)),  # Assuming 'date' contains both date and time information
        Column("start_time", String(16)),  # Adjust the length as needed
        Column("visiting_team", String(32)),  # Adjust the length based on expected team name length
        Column("visitor_score", Integer),
        Column("home_team", String(32), nullable=False),  # Renamed 'Home/Neutral' for clarity
        Column("home_score", Integer),
        Column("attendance", Integer),
        Column("arena", String(64))  # Adjust the length based on expected arena name length
    )

    # Create the table in the database
    metadata_obj.create_all(engine)

    df.columns = [col.strip() for col in df.columns]

    rows = df.to_dict(orient='records')

    #  Assuming 'game_stats_table' is the SQLAlchemy Table object you're inserting data into
    # Insert each row into the database
    for row in rows:
        # Note: Ensure your table column names and DataFrame column names match
        stmt = insert(game_stats_table).values(**row)
        with engine.begin() as connection:
            connection.execute(stmt)

    with engine.connect() as connection:
        cursor = connection.exec_driver_sql("SELECT * FROM game_stats")
        # print(cursor.fetchall())

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


    sql_database = SQLDatabase(engine, include_tables=["game_stats"])



    sql_query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=["game_stats"],
    )

    vector_indices = []
    documents = SimpleDirectoryReader("data").load_data()
    vector_indices.append(VectorStoreIndex.from_documents(documents))
    vector_query_engines = [index.as_query_engine() for index in vector_indices]

    from llama_index.core.tools import QueryEngineTool


    sql_tool = QueryEngineTool.from_defaults(
        query_engine=sql_query_engine,
        description=(
            "SQL database having information about each game for this season. It has the following columns"
            " Table contains the following Columns: ['date', 'start_time', 'visiting_team', ' visitor_score', 'home_team', 'home_score', 'attendance', 'arena']" 
            
        ),
    )
    vector_tools = []
    for query_engine in vector_query_engines:
        vector_tool = QueryEngineTool.from_defaults(
            query_engine=query_engine,
            description=f"Usefull for information regarding rules, norms, and defining the game",
        )
        vector_tools.append(vector_tool)

    query_engine = RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=([sql_tool] + vector_tools),
    )
    return query_engine