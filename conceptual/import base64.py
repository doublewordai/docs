import base64
import os
import random
import fitz  # PyMuPDF
import openai
import json
import pandas as pd 
import dash_bootstrap_components as dbc
from dash import (
    Dash, html, dcc, callback, Input, Output, State, no_update, ALL, callback_context,
    get_relative_path, dash_table
)
import logging
import dataiku
import tempfile
import shutil
from pathlib import Path 
from dash.exceptions import PreventUpdate
import urllib.parse, os.path
from flask import Response, abort, request
import base64
from functools import lru_cache
import ast
import re
from  dataiku.core.sql import SQLExecutor2
from dash_extensions import SSE
from dash_extensions.streaming import sse_message, sse_options
from openai import OpenAI
import datetime

def clean(s): return re.sub(r'^[^A-Za-z]+', '', s).strip()

app.config.suppress_callback_exceptions = True

logger = logging.getLogger(__name__)

WEBAPP_INPUTS = dataiku.Dataset("webapp_inputs")
input_df = WEBAPP_INPUTS.get_dataframe().dropna(subset=['variable_name']).set_index('variable_name')['variable_value'].to_dict()
logger.info(input_df)

############## VARIABLES TO EDIT ON HANDOVER ##################
REPORT_PDF_FOLDER = input_df["REPORT_PDF_FOLDER"]     # "elements_explorer_docs"
TMP_DOC_FOLDER_NAME = input_df["TMP_DOC_FOLDER_NAME"] # "elements-rag-tmp"
BASE_URL = input_df["BASE_URL"]                       # "https://app.doubleword.ai/ai/v1/"

# Use your DSS API key instead of an OpenAI secret
API_KEY = input_df["API_KEY"]                         # "sk-tiOkv9pzotCfHg4rV9QTcLdiwzV6imnGIWLoGE1FcXo"
TEXTBOOK_PDF_FOLDER= input_df["TEXTBOOK_PDF_FOLDER"]  # "textbooks"
KNOWLEDGE_BANK_ID = input_df["KNOWLEDGE_BANK_ID"]     # "KPOuzSuL"
SSE_URL = input_df["SSE_URL"]                         # f"{BASE_URL.rstrip('/')}/chat/completions"
SQL_CONNECTION = input_df["SQL_CONNECTION"]           #"ElementsSnowflakeDB"
TABLE_LOC = input_df["TABLE_LOC"]                     # '"ELEMENTSDEMODB"."PUBLIC"."EXTRACTEDDATA"'
USE_FAKE_REPORTS = int(input_df["USE_FAKE_REPORTS"])  # int("1")
FEEDBACK_DB_NAME = input_df["FEEDBACK_DB_NAME"]
MODEL_NAME = input_df["MODEL_NAME"]
SQL_DIALECT = input_df["SQL_DIALECT"]

OAI_CLIENT= OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)
###############################################################

##################### DIALECT AWARE SQL HELPERS ###############
def _dialect_quotechar(dialect: str) -> str:
    return '"' if str(dialect).lower() == "snowflake" else '`'

def _strip_wrapping_quotes(name: str) -> str:
    if not name:
        return name
    if (name.startswith('"') and name.endswith('"')) or (name.startswith('`') and name.endswith('`')):
        return name[1:-1]
    return name

def _quote_ident(name: str, dialect: str) -> str:
    q = _dialect_quotechar(dialect)
    core = _strip_wrapping_quotes(name)
    # Escape the quote char inside the identifier (Snowflake: "" ; Spark: ``)
    core = core.replace(q, q + q)
    return f"{q}{core}{q}"

def _quote_fqn(fqn: str, dialect: str) -> str:
    # Simple split on dots (assumes no dots inside parts)
    parts = [p.strip() for p in fqn.split('.')]
    parts = [_strip_wrapping_quotes(p) for p in parts]
    return '.'.join(_quote_ident(p, dialect) for p in parts)

def q(val):
    """Quote a Python value for SQL (single-quoted)."""
    if val is None:
        return "NULL"
    s = str(val).replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"

################################################################
logger.info(TABLE_LOC)
# UI / UX 

# Element brand colors
ELEMENT_BLUE = "#0074AD"
ELEMENT_RED = "#D42114"
ELEMENT_LIGHT_GRAY = "#F5F5F5"
ELEMENT_DARK_GRAY = "#333333"

def create_section_header(title):
    """Creates a consistently styled section header"""
    return dbc.CardHeader(
            html.H4(title, className="text-primary mb-0"),
            style={"backgroundColor": ELEMENT_LIGHT_GRAY}
    )


# Change Bootstrap theme to use a custom theme that matches Element's branding
app.config.external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css']


# ------ ACCESSING PDFS STORED IN S3 ---------
# We are storing pdf's that the model will access in a Dataiku 'Managed Folder'
# which is an abstraction over S3. We often need to access the pdfs for display 
# and editing. 

# We display the pdf's in iframe objects, and we edit them for
# highlighting chunks used by the model.

# To display them we cannot just save them locally and pass the file path to iframe.
# This is because the server and client components in dash don't necessarily share a 
# file system in Dataiku like they do when you run locally. So the iframe, which sits
# serverside (I think), needs another way to access the files.

# We give it access to the files by creating a flask endpoint that pulls the pdfs
# from S3 and streams it to the iframe. So the iframe requests a url like this:
# /some/dataiku/path/pdf/example_doc.pdf and it will be streamed directly from dataiku.
# --------------------------------------------
DOC_FOLDER = dataiku.Folder(REPORT_PDF_FOLDER)   # managed folder handle
@app.server.route("/pdf/<path:key>")
def stream_pdf(key):
    """
    One route that streams a file from the managed folder
    directly to the browser.
    """
    try:
        stream = DOC_FOLDER.get_download_stream(key)   # binary iterator
    except Exception:
        abort(404)

    return Response(stream, mimetype="application/pdf",
                    direct_passthrough=True)           

TMP_DOC_FOLDER = dataiku.Folder(TMP_DOC_FOLDER_NAME)   # managed folder handle
@app.server.route("/tmppdf/<path:key>")
def stream_tmp_highlighted_pdf(key):
    """
    One route that streams a file from the managed folder
    directly to the browser.
    """
    try:
        stream = TMP_DOC_FOLDER.get_download_stream(key)   # binary iterator
    except Exception:
        abort(404)

    return Response(stream, mimetype="application/pdf",
                    direct_passthrough=True)           

# This endpoint handles streaming the language model responses. 

@app.server.post("/stream")
def stream():
    message = request.data.decode("utf-8")
    message_json = ast.literal_eval(message)
    
    try:
        request_headers = dict(request.headers)
        auth_info_browser = dataiku.api_client().get_auth_info_from_browser_headers(request_headers)
        user = auth_info_browser["authIdentifier"]
    except:
        user = "could not identify user"
        

    custom_headers = {'X-User-ID': user}

    def oai_event_stream(msg):
        completion = OAI_CLIENT.chat.completions.create(
          model=MODEL_NAME,
          messages=msg,
          extra_headers=custom_headers,
          stream=True,
          stream_options={
             "include_usage": True
           },
        )
        
        for chunk in completion:
           # Safely handle the chunk using attribute-style access
            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    # Yield the content if it exists
                    yield sse_message(choice.delta.content)
                else:
                    # Log a warning only if the chunk is missing "delta.content"
                    logger.warning(f"Chunk missing 'delta.content': {chunk}")
            else:
                # Log a warning only if the chunk is missing "choices"
                logger.warning(f"Chunk missing 'choices': {chunk}")

        # Send an empty message to signal the end of the stream
        yield sse_message()
    
    # Add the 'X-Accel-Buffering' header for streaming to work.
    response = Response(oai_event_stream(message_json), mimetype="text/event-stream")
    response.headers["X-Accel-Buffering"] = "no"
    
    return response

app.clientside_callback(
    """function(x, current){
       return (current || "") + x
    }""",
    Output("pinned-md", "children", allow_duplicate=True), 
    Input("sse", "animation"),
    State("chat-display-history-store", "data"),    
    
    prevent_initial_call=True,
)

##Chat Scroll Down automatically
app.clientside_callback(
    """
    function(content) {
        const container = document.getElementById('pinned-md-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('pinned-md-container', 'children', allow_duplicate=True),  # Dummy output to satisfy callback
    Input('pinned-md', 'children'),
    prevent_initial_call=True,
)
####End Chat Scroll Section


# -------- RAG CHATBOT LAYOUT -------------- 

chat_panel = dbc.Offcanvas(
    id="chat-offcanvas",
    title="",
    is_open=False,
    scrollable=True,
    placement="end",
    style={"width": "42rem", "boxShadow": "0 0 20px rgba(0,0,0,0.1)"}, 
    children=[ 
        # Chat panel content (no PDF iframe here)
        dbc.Card([
            create_section_header("Chat"),
            dbc.CardBody([
                dcc.Store(id="selected-filters-store", data={"SourceFolder": []}),
                dcc.Store(id='chat-store', data={'history': [], 'is_bot_thinking': False, 'display_history':[]}),
                dcc.Store(id='pdf-store', data={'active_pdf': None}),
                dcc.Store(id='sources-store', data=[]),
                dcc.Store(id='chat-display-history-store', data=""),
                dcc.Store(id='rag-toggle',data={'use_rag':True}),
                SSE(id="sse", concat=True, animate_chunk=5, animate_delay=10),
                dcc.Store(id='feedback-store', data=[]),
               html.Div([
                html.Div([
                    html.Span("Include Reference Materials", 
                             style={"fontWeight": "500", "marginRight": "10px"}),
                    dbc.Switch(
                        id="include-documents-switch",
                        value=False,  # real default comes from rag-toggle via callback
                        className="mb-0 custom-switch",
                        labelClassName="switch-label",  
                    ),
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "8px"}),

                # Collapsible section for document type selection - only shown when switch is on
                html.Div([
                    html.Div("Select reference types:", 
                             style={"fontSize": "13px", "marginBottom": "6px", "color": "#666", "display": "none"}, 
                             id="reference-types-label"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checkbox(
                                id="ref-books-checkbox",
                                className="custom-checkbox",
                                value=False,
                                label="Books",
                            ),
                        ], width=6, style={"display": "none", "paddingRight": "4px"}, id="ref-books-container"),
                        dbc.Col([
                            dbc.Checkbox(
                                id="ref-specs-checkbox",
                                className="custom-checkbox",
                                value=False,
                                label="Specs",
                            ),
                        ], width=6, style={"display": "none", "paddingLeft": "4px"}, id="ref-specs-container"),
                    ], id="ref-row-1", className="g-0", style={"marginBottom": "4px"}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checkbox(
                                id="ref-papers-checkbox",
                                className="custom-checkbox",
                                value=False,
                                label="Reference",
                            ),
                        ], width=6, style={"display": "none", "paddingRight": "4px"}, id="ref-papers-container"),
                        dbc.Col([
                            dbc.Checkbox(
                                id="ref-reports-checkbox",
                                className="custom-checkbox",
                                value=True,
                                label="Filtered Reports",
                            ),
                        ], width=6, style={"display": "none", "paddingLeft": "4px"}, id="ref-reports-container"),
                       dbc.Col([
                            dbc.Checkbox(
                                id="all-ref-reports-checkbox",
                                className="custom-checkbox",
                                value=False,
                                label="All Reports",
                            ),
                        ], width=6, style={"display": "none", "paddingLeft": "4px"}, id="all-ref-reports-container"),
                    ], className="g-0", id="ref-row-2"),
                ], style={"padding": "0"}, id="reference-types-section"),
            ], style={
                "marginBottom": "12px", 
                "backgroundColor": "#f8f9fa", 
                "padding": "10px 12px", 
                "borderRadius": "6px",
                "border": "1px solid #e0e0e0",
            }),
            # Add this to your layout to warn that you can't have rag without selecting a source
            dbc.Toast(
                id="filter-warning-toast",
                header="Warning",
                children="You must select at least one reference source before proceeding.",
                icon="danger",  # Red icon for warning
                duration=4000,  # Auto-dismiss after 4 seconds
                is_open=False,
                dismissable=True,
                style={
                    "position": "fixed",
                    "top": 20,
                    "right": 20,
                    "zIndex": 2000,
                    "maxWidth": "320px"
                },
            ),
             # Pinned markdown (streaming)
              dbc.Card(
                dbc.CardBody(
                    dcc.Markdown(
                        id="pinned-md",
                        style={
                            "whiteSpace": "pre-wrap",
                            "margin": 0,
                            "overflowWrap": "anywhere",
                            "fontFamily": "'Segoe UI', system-ui, -apple-system, sans-serif",
                            "fontSize": "15px",
                            "lineHeight": "1.5",
                        },
                    ),
                    id="pinned-md-container",
                    style={
                        "maxHeight": "50vh",
                        "minHeight": "50vh",
                        "overflowY": "auto",
                        "padding": "16px",
                        "borderRadius": "8px",
                    },
                ),
                style={
                    "marginBottom": "16px",
                    "backgroundColor": "#ffffff",
                    "border": "1px solid #e0e0e0",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
                },
            ),

                # Sources (click to open highlighted page in shared viewer)
                html.Div(
                    id="sources-section",
                    children=[
                        html.Div([
                         html.H5("Sources", style={"margin": "0", "fontWeight": "600", "fontSize": "16px"}),
                            ], style={"marginBottom": "10px", "display": "flex", "alignItems": "center"}),
                            html.Div(
                                id="sources-container",
                                style={"display": "flex", "flexDirection": "column", "gap": "8px"}
                            )
                        ],
                    style={
                        "marginBottom": "16px",
                        "backgroundColor": "#ffffff",
                        "border": f"1px solid #e0e0e0",
                        "borderRadius": "8px",
                        "padding": "16px",
                        "maxHeight": "15vh",
                        "minHeight": "15vh",
                        "overflowY": "auto",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",

                    },
                ), 
            # Chat input area 
            html.Div([
                dbc.InputGroup([
                    dbc.Input(
                        id='chat-input',
                        type='text',
                        placeholder='Type a message...',
                        n_submit=0,
                        style={
                            "borderRadius": "8px 0 0 8px", 
                            "border": "1px solid #e0e0e0",
                            "padding": "12px 16px",
                            "fontSize": "15px",
                            "boxShadow": "none"
                        }
                    ),
                    dbc.Button(
                        'Send', 
                        id='send-button', 
                        n_clicks=0, 
                        style={
                            'backgroundColor': ELEMENT_BLUE, 
                            'borderRadius': '0 8px 8px 0',
                            'border': 'none',
                            'padding': '0 20px',
                        }
                    )
                ], style={"marginBottom": "8px"}), 
                
              # Add the Clear Conversation button
              html.Div([
                    dbc.Button(
                        "Clear Conversation",
                        id="clear-conversation-button",
                        color="secondary",
                        className="mb-3",
                        size = "sm",
                        style={
                                "backgroundColor": "#f8d7da",  # Light gray background
                                "color": "#721c24",  # Dark text
                                "border": "1px solid #f5c6cb",  # Subtle border
                                "borderRadius": "4px",  # Rounded corners
                                "padding": "4px 8px",  # Compact padding
                                "fontSize": "12px",  # Smaller font size
                                "textAlign": "center"} 
                    ),
                ], style={ "textAlign" : "center", "marginBottom": "8px"}),
        # Feedback
                html.Div(
                    id="feedback-section",
                    children=[
                        html.P("Was this conversation helpful?", style={"fontWeight": "500", "margin": "0 0 10px 0"}),
                       html.Div([
                        dbc.Button(
                            html.I("", className="fa fa-thumbs-up"), 
                            id="thumb-up", 
                            color="light", 
                            className="mr-3",
                            style={"marginRight": "10px", "borderRadius": "50%", "width": "40px", "height": "40px"}
                        ),
                        dbc.Button(
                            html.I("", className="fa fa-thumbs-down"), 
                            id="thumb-down", 
                            color="light",
                            style={"borderRadius": "50%", "width": "40px", "height": "40px"}
                        ),
                    ], style={"display": "flex", "justifyContent": "center"}),   
                     # Add a comment field
                    dbc.Collapse(
                        dbc.Form([
                                dbc.Label("Additional comments:", className="mt-3"),
                                dbc.Textarea(
                                    id="feedback-comment",
                                    placeholder="Please share any additional feedback...",
                                    style={"width": "100%", "height": "100px", "marginTop": "8px"}
                                ),
                                dbc.Button(
                                    "Submit Feedback", 
                                    id="submit-feedback", 
                                    color="primary", 
                                    className="mt-2",
                                    style={"backgroundColor": ELEMENT_BLUE}
                                )
                            ]),
                        id="feedback-comment-collapse",
                        is_open=False,
                    ),    
                    html.Div(id="feedback-confirmation", className="mt-2", style={"marginTop": "10px"})
                ],
                   style={
                    'textAlign': 'center', 
                    "padding": "16px", 
                    "backgroundColor": "#ffffff",
                    "border": "1px solid #e0e0e0",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
                    "marginTop": "16px",
                    "marginBottom": "16px"
                    }
                ),
            ], style={"padding": "16px 0"}),
        # Feedback toast + timer live inside the panel
        dcc.Interval(
            id="feedback-toast-timer",
            interval=2500,
            n_intervals=0,
            disabled=True,
            max_intervals=1,
        ),
        dbc.Toast(
            id="feedback-toast",
            header="Thanks!",
            is_open=False,
            dismissable=True,
            children="Your feedback was saved.",
            style={
                "position": "fixed",
                "top": 20,
                "right": 20,
                "zIndex": 2000,
                "maxWidth": "320px"
            },
        ),
    ])
  ])
 ])

app.clientside_callback(
    """
    function(is_open) {
        const body = document.body;
        if(is_open) {
            body.style.transition = 'padding-right 0.3s ease';
            body.style.paddingRight = '42rem';
            // Hide the backdrop that normally dims the screen
            const backdrop = document.querySelector('.offcanvas-backdrop');
            if(backdrop) backdrop.style.display = 'none';
        } else {
            body.style.paddingRight = '0';
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("body-shift-trigger", "data"),
    Input("chat-offcanvas", "is_open"),
    prevent_initial_call=True
)
    
# ------ RAG CHATBOT CALLBACKS -----------------------

# Callback 1. Include reference material toggle pops up reference types
@app.callback(
    [Output("reference-types-label", "style"),
     Output("ref-books-container", "style"),
     Output("ref-specs-container", "style"), 
     Output("ref-papers-container", "style"),
     Output("ref-reports-container", "style"),
     Output("all-ref-reports-container", "style")],
    Input("include-documents-switch", "value"),
    prevent_initial_call=False,
)
def toggle_reference_types_ui(switch_value):
    visible_style = {"display": "block", "fontSize": "13px", "marginBottom": "6px", "color": "#666"}
    hidden_style = {"display": "none"}
    
    col_visible = {"display": "block", "paddingRight": "4px"}
    col_visible_right = {"display": "block", "paddingLeft": "4px"}
    col_hidden = {"display": "none"}
    
    if switch_value:
        return visible_style, col_visible, col_visible_right, col_visible, col_visible_right, col_visible
    else:
        return hidden_style, col_hidden, col_hidden, col_hidden, col_hidden, col_hidden
    
# Callback 2. Saves which reference types are selected for filtered RAG 
@app.callback(
    Output("selected-filters-store", "data"),
    [
        Input("ref-books-checkbox", "value"),
        Input("ref-specs-checkbox", "value"),
        Input("ref-papers-checkbox", "value"),
        Input("ref-reports-checkbox", "value"),
        Input("all-ref-reports-checkbox", "value"),
    ],
)
def update_selected_filters(books, specs, papers, reports, all_reports):
    # Map checkbox values to their corresponding SourceFolder names
    filters = []
    if books:
        filters.append("Books")
    if specs:
        filters.append("Specs")
    if papers:
        filters.append("Reference")
    if reports:
        filters.append("Filtered Reports")
    if all_reports:
        filters.append("Reports")

    # Return the updated filters
    return {"SourceFolder": filters}

# Callback 3. Decides if rag is being used or not 
@app.callback(
    Output("include-documents-switch", "value"),
    Input("rag-toggle", "data"),
    prevent_initial_call=False,
)
def sync_switch_from_store(store):
    if isinstance(store, dict) and "use_rag" in store:
        return bool(store["use_rag"])
    return True  # default if store is missing/empty

# Update rag-toggle store whenever the user flips the switch
@app.callback(
    Output("rag-toggle", "data"),
    Input("include-documents-switch", "value"),
    State("rag-toggle", "data"),
)
def sync_store_from_switch(switch_value, store):
    store = store or {}
    new_value = bool(switch_value)
    # Avoid unnecessary updates to prevent churn
    if store.get("use_rag") == new_value:
        return no_update
    store["use_rag"] = new_value
    return store


# Callback 4: Handle user input. Just adds the message and triggers the bot.
@app.callback(
    [
        Output('pinned-md', 'children', allow_duplicate=True),
        Output('chat-display-history-store', 'data', allow_duplicate=True), 
        Output('chat-store', 'data'), 
        Output('chat-input', 'value'),
        Output('sources-store', 'data', allow_duplicate=True)
    ],
    [
        Input('send-button', 'n_clicks'),
        Input('chat-input', 'n_submit'),
        Input('clear-conversation-button', 'n_clicks')  # Add the clear button as an input
    ], 
    [
        State('chat-input', 'value'),
        State('chat-store', 'data'),
        State('pinned-md', 'children')
    ],
    prevent_initial_call=True,
)
def handle_user_input(n_clicks, n_submit, clear_clicks, user_input, chat_data, current):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update

    # Check which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # If the "Clear Conversation" button was clicked
    if triggered_id == 'clear-conversation-button':
        return "", "", {'history': [], 'is_bot_thinking': False, 'display_history': []}, "", []

    # If the user submitted a message
    if triggered_id in ['send-button', 'chat-input']:
        if not user_input:
            return no_update, no_update, no_update, no_update, no_update

        history = chat_data.get('history', [])
        display_history = chat_data.get('display_history', [])

        # If there's already assistant text rendered in pinned-md,
        # capture the last assistant turn into both history and display_history.
        if current:
            last_assistant_message = current.split("**Assistant:**")[-1]
            history.append({'role': "assistant", 'content': last_assistant_message})

            # NEW: keep display_history in sync with assistant turns (with dedupe)
            if not display_history or display_history[-1].get('role') != 'assistant' \
               or display_history[-1].get('content') != last_assistant_message:
                display_history.append({'role': 'assistant', 'content': last_assistant_message})

    # Add the new user turn
    history.append({'role': 'user', 'content': user_input})
    display_history.append({'role': 'user', 'content': user_input})

    chat_data['history'] = history
    chat_data['display_history'] = display_history
    chat_data['is_bot_thinking'] = True
    
    display_str = (current or '') + "\n\n-----------\n\n**User:** " + user_input + "\n\n-----------\n\n**Assistant:** "
    return display_str, display_str, chat_data, '', no_update


# Define the available documents in the chat-bot's search remit. 
RAG_PDF_SOURCE = dataiku.Folder(TEXTBOOK_PDF_FOLDER)
RAG_AVAILABLE_PDFS = RAG_PDF_SOURCE.list_paths_in_partition()
TMP_RAG_STORAGE = dataiku.Folder(TMP_DOC_FOLDER_NAME)

KB_ID = KNOWLEDGE_BANK_ID  # Replace with your KB id

kb = dataiku.KnowledgeBank(id=KB_ID,
    project_key=dataiku.api_client().get_default_project().project_key)

vector_store = kb.as_langchain_vectorstore()

def template_user_message(query, chunks):
    enriched_msg = """# CONTEXT:"""

    
    for i, chunk in enumerate(chunks):        
        page_content = chunk.page_content

        enriched_msg += f"""
        ## SOURCE NUMBER: {i+1}
        
        ### Chunk: {page_content}
        
        """
        
    enriched_msg += f"""# QUERY: {query}"""
    
    return enriched_msg
    
RAG_SYSTEM_PROMPT = """You are a helpful assistant in a RAG app designed to help with failure analysts. 
Users will send in requests to you which are enriched with information from textbooks and reports extracted using semantic search.
Respond to the query which is marked as #QUERY in the user request.
Respond using the information in the context, which is marked as #CONTEXT. 
The context is sourced from text books and papers on failure analysis. 
Each chunk is from a section or page of a text book. 
Not every chunk will be strictly relevant to the question, and there may be parsing errors in the chunks. 
Use the chunks to help inform your answers. 
If there is nothing relevant in the chunks to the question, try to answer the question and then inform the user that there was no information in the chunks. 
Be very brief in your answers, users want information quickly, and will use the textbook to get in-depth answers."""

CHAT_SYSTEM_PROMPT = """You are a helpful assistant.
Be brief in your answers."""

   
# Callback 5: Generate bot response and pre-highlight source PDFs.
@app.callback(
    Output("sse", "url", allow_duplicate=True),
    Output("sse", "options"),
    Output("sources-store", "data", allow_duplicate=True), 
    Output("filter-warning-toast", "is_open"),  # Open the warning toast
    Input('chat-store', 'data'),
    State("rag-toggle", "data"),
    State("pinned-md", "children"),    
    State("selected-filters-store", "data"),  # Get the selected filters
    State("filtered-reports-store", "data"),  # Get the filtered reports
    prevent_initial_call=True
)
def generate_bot_response(chat_data, use_rag, current_convo, selected_filters, filtered_reports):
    
    if not chat_data.get('is_bot_thinking'):
        return no_update, no_update, no_update, False
        
    # Target the OpenAI-compatible streaming endpoint

    messages = chat_data.get('history', [])
    
    if not messages:
        return no_update, no_update, no_update, False

    # --- Source Snippet and Highlighting Logic ---
    sources = []

    # FIX: use messages, not undefined `history`
    assert messages[-1]["role"] == "user", "Last message should be a user message"
    user_msg = messages[-1]["content"]

    logger.info(f"USE RAG: {use_rag}") 
    if use_rag.get("use_rag", True):
        # Extract the selected filters
        source_filters = selected_filters.get("SourceFolder", [])
        if not source_filters:
            return no_update, no_update, no_update, True  # Open the warning toast
        logger.info(f"Source Filters: {source_filters}") 
        # Construct the filter
        if "Filtered Reports" in source_filters and filtered_reports:
            # Combine SourceFolder and file filters using $or
            search_filter = {"file": filtered_reports}
        
        else:
            # Only filter by SourceFolder
            search_filter = {"SourceFolder": {"$in": source_filters}}
        logger.info(f"Search filter: {search_filter}") 
        # Search for snippets that match the user query.
        search_result = vector_store.similarity_search(
            user_msg,
            k=3,  # Number of results to bring back
            filter=search_filter,   # optionally filter on metadata
        )

        user_msg_enriched = template_user_message(user_msg, search_result)
        messages[-1]["content"] = user_msg_enriched
        messages = [{"role":"system","content":RAG_SYSTEM_PROMPT}] + messages
        
        logger.info(messages)
        
        for i, chunk in enumerate(search_result):
            logger.info("THE SEARCH RESULTS")
            logger.info(chunk.metadata)
            chunk_metadata = ast.literal_eval(chunk.metadata["metadata"])
            available_metadata = list(chunk_metadata.keys())
            
            has_headers = "Headers" in available_metadata
            has_source_folder = "SourceFolder" in available_metadata
            
            logger.info("WHATS IN METADATA")
            logger.info(f"has_headers: {has_headers}")
            logger.info(f"has_source_folder: {has_source_folder}")
            
            if (not has_headers) and (not has_source_folder):
                logger.info("No Header or Source Folder found - check chunk quality")
            
            if has_headers:
                logger.info("IT HAS HEADERS")
                
                header_json = chunk_metadata["Headers"]
                header_keys = list(header_json.keys())

                logger.info(header_json)
                
                is_sectioned_doc = "headers" in header_keys
                is_paginated_doc = "page" in header_keys
                
                logger.info(f"is_sectioned: {is_sectioned_doc}")
                logger.info(f"is_paginated: {is_paginated_doc}")
                
                if is_sectioned_doc:
                    headers = header_json["headers"][-1]
                    section_type = "section"
                elif is_paginated_doc:
                    headers = f"Page {header_json['page']}"
                    section_type = "page"
                else:
                    logger.info("Neither header nor page available in header json - check chunk quality")
                    continue
                    
                logger.info("If we are here, we should have headers")
                logger.info(f"Headers: {headers}")
                
            else:
                logger.info("Cannot show source for chunk without header - check chunk quality")
                continue
                
            selected_pdf_name = chunk.metadata.get("file")
            logger.info(f"Selected PDF Name: {selected_pdf_name}")
            if not selected_pdf_name:
                continue

            with RAG_PDF_SOURCE.get_download_stream(selected_pdf_name) as stream:
                pdf_bytes = stream.read()

            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc_for_snippets:
                if section_type == "section" and headers:
                    toc = doc_for_snippets.get_toc()
                    matches = [(p - 1, t) for lvl, t, p in toc if t and t.strip().lower() == headers.lower()]
                    if not matches:
                        continue
                    page_idx, doc_title = matches[0]
                    try:
                        page = doc_for_snippets.load_page(page_idx)
                    except Exception:
                        continue

                    text_instances = page.search_for(clean(doc_title))
                    for inst in text_instances or []:
                        highlight = page.add_highlight_annot(inst)
                        highlight.update()

                    output_pdf_name = f"highlighted_source_{i}.pdf"
                    TMP_RAG_STORAGE.upload_data(output_pdf_name, doc_for_snippets.tobytes())

                    sources.append({
                        "snippet": doc_title,
                        "highlighted_file": output_pdf_name,
                        "page_num": page_idx,
                        "file_name": selected_pdf_name
                    })
                elif section_type == "page":
                    # Optional: basic page-level "source" without a specific highlight
                    # Convert human-readable page number (1-based)
                    # Here we skip highlights and just link that page.
                    try:
                        page_num_zero_based = int(header_json["page"]) - 1
                    except Exception:
                        page_num_zero_based = 0

                    output_pdf_name = f"highlighted_source_{i}.pdf"
                    # Even if no highlights, persist a copy for consistent serving
                    TMP_RAG_STORAGE.upload_data(output_pdf_name, doc_for_snippets.tobytes())

                    sources.append({
                        "snippet": headers + " in " + selected_pdf_name.split("/")[-1],
                        "highlighted_file": output_pdf_name,
                        "page_num": page_num_zero_based,
                        "file_name": selected_pdf_name
                    })

    else:
        messages = [{"role":"system","content":CHAT_SYSTEM_PROMPT}] + messages
    # Request body: stream must be True for SSE/chunked responses
    if False:
        completion = OAI_CLIENT.chat.completions.create(
          model=MODEL_NAME,
          messages=messages,
          stream=False
        )
        

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    url = get_relative_path("/stream") 
    
    logger.info("Sources List:")
    logger.info(sources)
    
    # Return both the SSE config and the sources list for rendering
    return url, sse_options(json.dumps(messages), headers=headers, method="POST"), sources, False

    
# Callback 6: Renders sources in chatbot
    
@app.callback(
    [Output("sources-container", "children"),
     Output("sources-section", "style")],  # Add style output to control visibility
    Input("sources-store", "data")
)
def render_sources(sources):
    # Base style for the sources section
    base_style = {
        "marginBottom": "16px",
        "backgroundColor": "#ffffff",
        "border": f"1px solid #e0e0e0",
        "borderRadius": "8px",
        "padding": "16px",
        "maxHeight": "15vh",
        "minHeight": "15vh",
        "overflowY": "auto",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
    }
    
    # If no sources or RAG is disabled, hide the section completely
    if not sources:
        hidden_style = {**base_style, "display": "none"}
        return [html.Div("No sources available.")], hidden_style
    
    buttons = []
    for i, src in enumerate(sources, start=1): 
        # Extract and format the file name
        file_path = src.get("file_name", "Unknown File")
        file_name = file_path.split("/")[-1]  # Extract the file name
        # Format the page number (convert from 0-based to 1-based)
        page_num = src.get("page_num", 0) + 1
        # Get the snippet
        snippet = src.get("snippet", "No snippet available")
        
        # Format the source
        source_text = f"[{i}] {file_name}, Page {page_num}, \"{snippet}\""
        
         # Create the button for the source
        buttons.append(
            html.Button(
                source_text,
                id={
                    "type": "source-button",
                    "index": json.dumps(src)
                },
                style={
                    "display": "block",
                    "textAlign": "left",
                    "border": f"1px solid {ELEMENT_BLUE}",
                    "borderRadius": "5px",
                    "width": "100%",
                    "backgroundColor": ELEMENT_LIGHT_GRAY,
                    "color": ELEMENT_DARK_GRAY,
                    "padding": "8px",
                    "fontStyle": "italic",
                },
            )
        )
    return buttons, base_style

    
# Callback 7: Handle source button clicks. This is now very fast.
@app.callback(
    Output('pdf-store', 'data'),
    Input({'type': 'source-button', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_source_click(n_clicks):
    logger.info("Handling Source Click")
    
    if not any(n_clicks):
        return no_update

    ctx = callback_context
    if not ctx.triggered_id:
        return no_update

    source_data_str = ctx.triggered_id['index']
    logger.info(f"Source Data: {source_data_str}")
    
    try:
        source_data = json.loads(source_data_str)
    except json.JSONDecodeError as e:
        logger.info(f"Error loading source: {e}")
        return no_update
    
    
    highlighted_file = source_data['highlighted_file']
    page_num = source_data['page_num']
    
    active_pdf = f"{highlighted_file}#page={page_num + 1}"
    
    logger.info(f"Source Data: {source_data}")
    logger.info(f"Highlighted File: {highlighted_file}")
    logger.info(f"Page Num: {page_num}")
    logger.info(f"Active PDF: {active_pdf}")
    
    return {'active_pdf': highlighted_file, 'page_num': page_num+1, 'version': random.random()}

# Callback 8: Update the PDF viewer when the pdf-store changes.
@app.callback(
    Output('explorer-pdf-viewer', 'src'),
    Input('pdf-store', 'data'),
    Input('pdf-table', 'active_cell'),
    State('pdf-table', 'data'),
    prevent_initial_call=True
)
def update_shared_pdf_viewer(pdf_data, active_cell, table_data):
    # If a source button in Chat was clicked, pdf-store will contain a highlighted tmp PDF
    from dash import callback_context as ctx
    trig = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    logger.info(f"Triggered by {trig}")
    
    if trig == 'pdf-store' and isinstance(pdf_data, dict):
        active_pdf = pdf_data.get('active_pdf')
        logger.info(f"Active pdf {active_pdf}")
        
        page_num = pdf_data.get('page_num', 1)
        logger.info(f"Page Num {page_num}")
        
        if active_pdf:
            pdf_loc = urllib.parse.quote(active_pdf, safe="/")
            logger.info(f"pdf loc: {pdf_loc}" )
            return get_relative_path(f"/tmppdf/{pdf_loc}") + f"#page={page_num}"

    # Otherwise, a row in the Explorer table was clicked
    if active_cell and table_data:
        row = table_data[active_cell["row"]]
        if USE_FAKE_REPORTS:
            pdf_key = "example_doc.pdf"
        else:
            logger.info(row)
            pdf_key = row["file_val"] # if SQL_DIALECT =="snowflake" else row["file_val"]
        return get_relative_path(f"/pdf/{urllib.parse.quote(pdf_key)}")

    raise PreventUpdate

# Callback 9: Toggles the chatbot open / closed
@app.callback(
    Output("chat-offcanvas", "is_open"),
    Output("sse", "url", allow_duplicate=True),
    Output("chat-display-history-store", "data", allow_duplicate=True),
    
    Input("open-chat", "n_clicks"),
    State("chat-offcanvas", "is_open"),
    State("pinned-md", "children"),

    prevent_initial_call=True
)
def toggle_chat(n_open, is_open, chat_state):
    n_open = n_open or 0
    if n_open:
        return not is_open, None, chat_state 
    return is_open, None, chat_state

## added for resizing 

@app.callback(
    [
        Output("filter-column", "style"),
        Output("report-list-column", "style"),
        Output("document-viewer-column", "style"),
    ],
    Input("chat-offcanvas", "is_open"),
)
def toggle_sections(is_chat_open):
    if is_chat_open:
        # Hide filters and report list, expand PDF viewer
        return (
            {"display": "none"},  # Hide filters
            {"display": "none"},  # Hide report list
            {"width": "100%"},  # Expand PDF viewer to full width
        )
    else:
        # Show filters and report list, restore original layout
        return (
            {"display": "block", "width": "25%"},  # Show filters
            {"display": "block", "width": "50%"},  # Show report list
            {"width":  "50%"},    # Restore PDF viewer width
        )


# Callback 10: Handle feedback buttons / collection

# Initialize a global DataFrame for feedback
feedback_ds = dataiku.Dataset(FEEDBACK_DB_NAME, ignore_flow=True)
feedback_ds.spec_item["appendMode"] = True

# Add this callback to show comment field when thumbs up/down is clicked
@app.callback(
    Output("feedback-comment-collapse", "is_open", allow_duplicate=True),
    [Input("thumb-up", "n_clicks"), 
     Input("thumb-down", "n_clicks")],
    [State("feedback-comment-collapse", "is_open")],
    prevent_initial_call=True, 
    callback_group="toggle_callback_group"
)
def toggle_comment_box(up_clicks, down_clicks, is_open):
    if up_clicks or down_clicks:
        return True
    return is_open

@app.callback(
    [
        Output('feedback-toast', 'is_open'),
        Output('feedback-toast', 'children'),
        Output('feedback-toast-timer', 'disabled'),
        Output('feedback-confirmation', 'children'),  # keep the old div but leave it empty
        Output('feedback-comment', 'value'),
        Output('thumb-up', 'color'),  # Reset thumbs-up button color
        Output('thumb-down', 'color'),  # Reset thumbs-down button color
        Output('feedback-comment-collapse', 'is_open', allow_duplicate=True),
        Output('feedback-store', 'data')

    ],
    [
        Input('thumb-up', 'n_clicks'),
        Input('thumb-down', 'n_clicks'),
        Input('submit-feedback', 'n_clicks')
    ],
    [
        State('chat-store', 'data'),
        State('pinned-md', 'children'), # to capture the latest streamed assistant turn
        State('feedback-comment', 'value'),
        State('feedback-store', 'data') 
    ],
    prevent_initial_call=True, 
    callback_group="feedback_group"
)
def save_feedback(n_clicks_up, n_clicks_down, submit_clicks, chat_data, pinned_md, comment, feedback_store):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Initialize feedback_store if it's None
    feedback_store = feedback_store or {}
    
    # If thumbs-up or thumbs-down is clicked but not submit, highlight the button
    if button_id == 'thumb-up':
        feedback_store['rating'] = 1
        return no_update, no_update, no_update, "Please add any comments and click Submit", no_update, "success", "light", True, feedback_store
    elif button_id == 'thumb-down':
        feedback_store['rating'] = 0
        return no_update, no_update, no_update, "Please add any comments and click Submit", no_update, "light", "danger", True, feedback_store
        
     # If submit-feedback is clicked
    if button_id == 'submit-feedback':
        history = chat_data.get('display_history', []) or []

        # Ensure the latest streamed assistant text is included
        final_history = list(history)
        if pinned_md and "**Assistant:**" in pinned_md:
            last_assistant_message = pinned_md.split("**Assistant:**")[-1]
            if not final_history or final_history[-1].get('role') != 'assistant' \
               or final_history[-1].get('content') != last_assistant_message:
                final_history.append({'role': 'assistant', 'content': last_assistant_message})

        if not final_history:
            # Show an ephemeral error toast instead of overlapping text in the card
              return True, "Cannot give feedback on an empty chat.", False, "", "", "light", "light"

                # Retrieve the rating from the store
        rating = feedback_store.get('rating', None)
        
        if rating is None:
            return True, "Please select thumbs-up or thumbs-down before submitting feedback.", False, "", "", "light", "light", True, feedback_store

        # Get current user and timestamp
        try:
            # Get current user from Dataiku API
            request_headers = dict(request.headers)
            auth_info_browser = dataiku.api_client().get_auth_info_from_browser_headers(request_headers)
            username = auth_info_browser["authIdentifier"]
        except:
            # Fallback if API call fails
            username = "unknown_user"

        # Get current timestamp
        timestamp = datetime.datetime.now().isoformat()

        new_row = pd.DataFrame([pd.Series({
            'conversation_history': json.dumps(final_history),
            'rating': rating,
            'comment': comment or None, 
            'timestamp': timestamp,
            'username' : username
        })])
        feedback_ds.write_with_schema(new_row)

        # Open toast + start timer; clear the in-card confirmation text
        return True, "Thank you for your feedback!", False, "", "", "light", "light", False, {}
      
    return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, feedback_store

# ----------- DOCUMENT EXPLORER LAYOUT ---------------

# ---------- LOAD DOCUMENT FILTERING DATASET --------------
# This dataframe holds the extracted values from the reports that then
# give us the filters that we use to select the documents.
# ---------------------------------------------------------
executor = SQLExecutor2(connection=SQL_CONNECTION)  # your DSS connection name

def unique_vals_in_column_with_dialect(column, table_loc, dialect="snowflake", cast_len=75):
    col = _quote_ident(column, dialect)
    tbl = _quote_fqn(table_loc, dialect)

    sql = f"""
    WITH vals AS (
      SELECT TRIM(SUBSTR(CAST({col} AS STRING), 1, {int(cast_len)})) AS v
      FROM {tbl}
      WHERE
        {col} IS NOT NULL
        AND NOT ({col} != {col})      -- filters IEEE NaN in both Snowflake & Spark
        AND UPPER(TRIM(CAST({col} AS STRING))) <> 'NAN'
    )
    SELECT DISTINCT v AS label, v AS value
    FROM vals
    WHERE v <> ''
    ORDER BY value;
    """
    return (executor.query_to_df(sql)
            .rename(columns=str.lower)
            .dropna(subset=["value", "label"])
            .sort_values("value")
            .to_dict(orient="records"))

# Snowflake
# industry_options = unique_vals_in_column(
#     "Industry",
#     '"ELEMENTSDEMODB"."PUBLIC"."node_ed947797_ELEMENTSTESTPROJECT_EXTRACTED_DATA"',
#     dialect="snowflake",
# )

# Databricks / Spark SQL (adjust catalog/schema/table)
# industry_options = unique_vals_in_column(
#     "Industry",
#     "hive_metastore.default.node_ed947797_elementstestproject_extracted_data",
#     dialect="databricks",
# )

def unique_vals_in_column(column):
    return unique_vals_in_column_with_dialect(column, TABLE_LOC, SQL_DIALECT)


# actual values for filter
facility_options = unique_vals_in_column("LabLocation")
industry_options = unique_vals_in_column("Industry")
base_material_options = unique_vals_in_column("BaseMaterial")
author_options = unique_vals_in_column("Author")
customer_name_options = unique_vals_in_column("Customer")
detailed_material_options = unique_vals_in_column("DetailedMaterial")
failure_mechanism_options = unique_vals_in_column("FailureMode")
failure_env_options = unique_vals_in_column("llm_output_FailureEnvironment")
sample_type_options = unique_vals_in_column("SampleType")
condition_type_options = unique_vals_in_column("Condition")
spec_options = unique_vals_in_column("Specs")
testing_options = unique_vals_in_column("Testing")
failure_options = unique_vals_in_column("FailureMode")

# style for tag badges
BADGE_STYLE = {
    'display'      : 'inline-block',
    'background'   : '#e0e0e0',
    'color'        : '#555',
    'borderRadius' : '4px',
    'padding'      : '2px 6px',
    'marginRight'  : '4px',
    'marginTop'    : '2px',
    'fontSize'     : '12px',
}


def get_min_max_years():
    sql = f"""
    SELECT MIN(YEAR(CAST("CreationDate_parsed" AS DATE))) AS min_year, MAX(YEAR(CAST("CreationDate_parsed" AS DATE))) AS max_year
    FROM {_quote_fqn(TABLE_LOC, SQL_DIALECT)}
    """
    year_range_df = executor.query_to_df(sql)
    min_year = int(year_range_df["MIN_YEAR"].iloc[0])
    max_year = int(year_range_df["MAX_YEAR"].iloc[0])
    return min_year, max_year

# Make years dynamic
min_year, max_year = get_min_max_years()


# Generate marks for every 5 years and ensure max_year is included
marks = {year: str(year) for year in range(min_year, max_year + 1, 5)}
if max_year not in marks:
    marks[max_year] = str(max_year)  # Explicitly add the max_year to the marks

# Create date filter
year_slider = dbc.Form([
            # Add the Clear Filters button
        html.Div([
             dbc.Button(
                "Clear Filters",
                id="clear-filters-button",
                color="danger",
                size="sm",
                style={
                    "fontSize": "12px",
                    "padding": "4px 8px",
                    "marginBottom": "8px",
                    "borderRadius": "4px",
                    "backgroundColor": "#f8d7da",  # Light red background
                    "color": "#721c24",  # Dark red text
                    "border": "1px solid #f5c6cb",  # Subtle border
                }
            )
        ],
            style={"textAlign": "right"}  # Align the button to the left
        ),
    dbc.Label("Date Range", className="font-weight-bold mb-2"),
    dcc.RangeSlider(
        id="year-slider",
        min=min_year,  # Default start date (can be set dynamically)
        max=max_year,    # Default end date (can be set dynamically)
        step=1,  # Step size is one day (in seconds)
        value=[min_year, max_year],  # Default range
        marks=marks, 
        tooltip={"placement": "bottom", "always_visible": False},
        className="mb-3",
    )
])

# Create multi-select dropdowns each filter 
author_dropdown = dbc.Form([
    dbc.Label("Author", className="font-weight-bold mb-2"),
    dcc.Dropdown(
        id='author-dropdown',
        options=author_options,
        multi=True,
        placeholder='Select authors...',
        className="mb-3", 
        searchable=True, clearable=True
    )
])

customer_dropdown = dbc.Form([
    dbc.Label("Customer Name", className="font-weight-bold mb-2"),
    dcc.Dropdown(
        id='customer-dropdown',
        options=customer_name_options,
        multi=True,
        placeholder='Select customers...',
        className="mb-3", 
        searchable=True, clearable=True
    )
])

facility_selector = dbc.Form([
        dbc.Label("Facility", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='facility-dropdown',
            options=facility_options,
            multi=True,
            placeholder='Select a facility...',
            className="mb-3", 
            searchable=True, clearable=True
        ),
    ])

detailed_material_selector = dbc.Form([
        dbc.Label("Detailed Materials", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='detailed-material-dropdown',
            options=detailed_material_options,
            placeholder='Select detailed material...',
            multi=True,
            className="mb-3", 
            searchable=True, clearable=True
        ),
    ])

sample_selector = dbc.Form([
        dbc.Label("Sample Type", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='sample-dropdown',
            options=sample_type_options,
            placeholder='Select sample...',
            multi=True,
            className="mb-3",
            searchable=True, clearable=True
        ),
    ])

condition_selector = dbc.Form([
        dbc.Label("Condition", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='condition-dropdown',
            options=condition_type_options,
            placeholder='Select condition...',
            multi=True,
            className="mb-3", 
            searchable=True, clearable=True
        ),
    ])

spec_selector = dbc.Form([
        dbc.Label("Spec", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='spec-dropdown',
            options=spec_options,
            placeholder='Select spec...',
            multi=True,
            className="mb-3",
            searchable=True, clearable=True
        ),
    ])

testing_selector = dbc.Form([
        dbc.Label("Testing", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='testing-dropdown',
            options=testing_options,
            placeholder='Select testing...',
            multi=True,
            className="mb-3",
            searchable=True, clearable=True
           
        ),
    ])
industry_selector = dbc.Form([
        dbc.Label("Industry", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='industry-dropdown',
            options=industry_options,
            multi=True,
            placeholder="Select industries...",
            className="mb-3",
            searchable=True, clearable=True
        )
    ])

base_material_selector =  dbc.Form([
        dbc.Label("Base Material", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='base-material-dropdown',
            options=base_material_options,
            multi=True,
            placeholder="Select base material...",
            className="mb-3",
            searchable=True, clearable=True
        )
    ])

failure_mechanism_selector = dbc.Form([
        dbc.Label("Failure Mechanism", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='failure-dropdown',
            options=failure_options,
            multi=True,
            placeholder="Select failure mechanism...",
            className="mb-3",
            searchable=True, clearable=True
        )])

failure_environment_selector = dbc.Form([
        dbc.Label("Failure Environment", className="font-weight-bold mb-2"),
        dcc.Dropdown(
            id='failure-env-dropdown',
            options=failure_env_options,
            multi=True,
            placeholder="Select failure environment...",
            className="mb-3",
            searchable=True, clearable=True
        )])


filter_components = [
    year_slider,
    facility_selector,
    industry_selector,
    author_dropdown, 
    customer_dropdown,
    base_material_selector,
    detailed_material_selector,
    failure_mechanism_selector,
    failure_environment_selector,
    sample_selector,
    condition_selector,
    spec_selector,
    testing_selector
]

## Callback to clear filters
@app.callback(
    [
        Output('facility-dropdown', 'value'),
        Output('industry-dropdown', 'value'),
        Output('base-material-dropdown', 'value'),
        Output('author-dropdown', 'value'),
        Output('customer-dropdown', 'value'),
        Output('detailed-material-dropdown', 'value'),
        Output('sample-dropdown', 'value'),
        Output('condition-dropdown', 'value'),
        Output('spec-dropdown', 'value'),
        Output('testing-dropdown', 'value'),
        Output('failure-dropdown', 'value'),
        Output('failure-env-dropdown', 'value'),
        Output('year-slider', 'value'),  # Add the range slider output
    ],
    Input('clear-filters-button', 'n_clicks'),
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    # Reset all dropdowns to None
    return [None] * 12 + [[min_year, max_year]]

# ------ DOCUMENT EXPLORER LAYOUT -----------------------

explorer_layout = html.Div([
    dcc.Store(id="filtered-reports-store", data=[]),
    dbc.Row([
        dbc.Col(width=3),
        dbc.Col(html.H2("Document Explorer", style={'textAlign': 'center', 'marginBottom': '20px'}), width=6, className="text-center"),
        dbc.Col(
            dbc.Button("Toggle Chat", id="open-chat", color="primary", className="float-end mb-3"),
            width=3
        ),
    ],align="center"),
    
    dbc.Row([
        # Filters on the left
        dbc.Col([
            dbc.Card([
           create_section_header("Filters"),
            dbc.CardBody([
                    *filter_components
                ], style={"height": "75vh", "overflowY": "auto"})
            ], className="h-100")
        ], id = "filter-column", width=3, className="px-1 filter-column"), 
                # Report List Column
               # Grouped Report List and Document Viewer Column
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        create_section_header("Report List"),
                        dbc.CardBody([
                            html.Div(
                                [
                                    html.Span(id="report-count", children="Showing 0 Reports", className="fw-semibold"),
                                ],
                                id="report-count-container",
                                className="d-flex justify-content-end text-muted small px-2 py-1"
                            ),
                            # PDF list container
                            dcc.Loading(
                                id="pdf-loader",
                                type="default",                 # 'default' | 'circle' | 'dot' | 'cube' | 'graph'
                                delay_show=300,                # avoid flicker
                                delay_hide=300,
                                overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                                children = html.Div(id='explorer-pdf-list-container')
                            )
                        ],
                            style={"height":"75vh", "padding": "0"}
                        )
                    ], className="h-100")
                ], id="report-list-column", width=12, className="px-1"),
                
                # PDF Viewer
                dbc.Col([
                        dbc.Card([
                            create_section_header("Document"),
                            dbc.CardBody(
                              dcc.Loading(
                                id = "pdf-loading", 
                                type = "default",
                                children=html.Iframe(id='explorer-pdf-viewer', style={
                                    'width': '100%', 
                                    'height': '75vh',
                                    'border': 'none'
                                })),
                              style={"padding": "0"}
                            )
                    ], className="h-100")
                ],id="document-viewer-column",width=12, className="px-1")
            ], className="g-1"),
              ], id="content-column", width=9, className="px-1")
    ], className="g-1")
], style={'padding': '10px'})

# ------ DOCUMENT EXPLORER CALLBACKS -----------------------
    

# Helper Functions for SQL filtering. 

def make_pdf_where(
    facility=None, industry=None, base_material=None,
    authors=None, customers=None, detailed_materials=None, samples=None,
    conditions=None, specs=None, testings=None, failure_mode=None, failure_env=None,
    start_date=None, end_date=None,
    *, dialect="snowflake", 
):
    C = {
        "facility": "LabLocation",
        "industry": "Industry",
        "base_material": "BaseMaterial",
        "author": "Author",
        "customers": "Customer",
        "detailed_material": "DetailedMaterial",
        "sample_type": "SampleType",
        "condition": "Condition",
        "specs": "Specs",
        "testing": "Testing",
        "failure_mode": "FailureMode",
        "failure_env": "llm_output_FailureEnvironment",
        "report_date": "CreationDate_parsed"
    }

    def cid(key): return _quote_ident(C[key], dialect)

    preds = []

    # multi-selects
    def _in_list(colkey, values):
        vals = [q(v) for v in values if v not in (None, "")]
        if vals:
            preds.append(f"{cid(colkey)} IN ({', '.join(vals)})")

    if facility:
        _in_list("facility", facility)
    if industry:
        _in_list("industry", industry)
    if base_material:
        _in_list("base_material", base_material)
    if authors:
        _in_list("author", authors)
    if customers:
        _in_list("customers", customers)
    if detailed_materials:
        _in_list("detailed_material", detailed_materials)
    if samples:
        _in_list("sample_type", samples)
    if conditions:
        _in_list("condition", conditions)
    if specs:
        _in_list("specs", specs)
    if testings:
        _in_list("testing", testings)
    if failure_mode:
        _in_list("failure_mode", failure_mode)
    if failure_env:
        _in_list("failure_env", failure_env)
     # Add date range filtering
    if start_date:
        preds.append(f"{cid('report_date')} >= {q(start_date)}")
    if end_date:
        preds.append(f"{cid('report_date')} <= {q(end_date)}")

    return " AND ".join(preds) or "1=1"

# ---------- Full SQL generator (uses unified helpers) ---------------------

def PDF_LIST_SQL_with_dialect(kwargs, table_loc, dialect="snowflake", cast_len=50):
    C = {
        "file": "file",
        "base_material": "BaseMaterial",
        "industry": "Industry",
        "report_title": "TitleoftheReport",
        "facility": "LabLocation",
        "author": "Author",
        "customer": "Customer",       
        "detailed_material": "DetailedMaterial",
        "sample_type": "SampleType",
        "condition": "Condition",
        "specs": "Specs",
        "testing": "Testing",
        "failure_mode": "FailureMode",
        "failure_env": "llm_output_FailureEnvironment",
        "report_num": "ReportNumber",
        "creation_date": "CreationDate_parsed"
    }

    def cid(key): return _quote_ident(C[key], dialect)
    def castN(col_ident): return f"TRIM(SUBSTR(CAST({col_ident} AS STRING), 1, {int(cast_len)}))"

    where_sql = make_pdf_where(dialect=dialect, **kwargs)
    tbl = _quote_fqn(table_loc, dialect)

    return f"""
WITH filtered AS (
  SELECT 
    {castN(cid('file'))}               AS file_val,
    {castN(cid('base_material'))}      AS basematerial_val,
    {castN(cid('industry'))}           AS industry_val,
    {castN(cid('report_title'))}       AS report_name,
    {castN(cid('facility'))}           AS facility,
    {castN(cid('author'))}             AS author,
    {castN(cid('customer'))}           AS customer_name,
    {castN(cid('detailed_material'))}  AS detailed_material,
    {castN(cid('sample_type'))}        AS sample_type,
    {castN(cid('condition'))}          AS condition,
    {castN(cid('specs'))}              AS specs,
    {castN(cid('testing'))}            AS testing,
    {castN(cid('failure_mode'))}       AS failure_mode,
    {castN(cid('failure_env'))}        AS failure_env,
    {castN(cid('report_num'))}         AS report_num,
    {castN(cid('creation_date'))}      AS creation_date
  FROM {tbl}
  WHERE {where_sql}
)
SELECT DISTINCT
  file_val, basematerial_val, industry_val, report_name,
  facility, author, customer_name, detailed_material,
  sample_type, condition, specs, testing, failure_mode, failure_env, report_num, creation_date
FROM filtered
WHERE (file_val IS NOT NULL AND file_val <> '' AND UPPER(file_val) <> 'NAN')
   OR (basematerial_val IS NOT NULL AND basematerial_val <> '' AND UPPER(basematerial_val) <> 'NAN')
   OR (industry_val IS NOT NULL AND industry_val <> '' AND UPPER(industry_val) <> 'NAN')
   OR (report_name IS NOT NULL AND report_name <> '' AND UPPER(report_name) <> 'NAN')
   OR (facility IS NOT NULL AND facility <> '' AND UPPER(facility) <> 'NAN')
   OR (author IS NOT NULL AND author <> '' AND UPPER(author) <> 'NAN')
   OR (customer_name IS NOT NULL AND customer_name <> '' AND UPPER(customer_name) <> 'NAN')
   OR (detailed_material IS NOT NULL AND detailed_material <> '' AND UPPER(detailed_material) <> 'NAN')
   OR (sample_type IS NOT NULL AND sample_type <> '' AND UPPER(sample_type) <> 'NAN')
   OR (condition IS NOT NULL AND condition <> '' AND UPPER(condition) <> 'NAN')
   OR (specs IS NOT NULL AND specs <> '' AND UPPER(specs) <> 'NAN')
   OR (testing IS NOT NULL AND testing <> '' AND UPPER(testing) <> 'NAN')
   OR (failure_mode IS NOT NULL AND failure_mode <> '' AND UPPER(failure_mode) <> 'NAN')
   OR (failure_env IS NOT NULL AND failure_env <> '' AND UPPER(failure_env) <> 'NAN')
   OR (report_num IS NOT NULL AND report_num <> '' AND UPPER(report_num) <> 'NAN')
"""

def PDF_LIST_SQL(kwargs):
    return PDF_LIST_SQL_with_dialect(kwargs, table_loc=TABLE_LOC, dialect=SQL_DIALECT)

def camel_to_kebab(s):  # reuse if you already have it
    return "".join("-" + c.lower() if c.isupper() else c for c in s)

def dict_to_css(d):
    return "; ".join(f"{camel_to_kebab(k)}: {v}" for k, v in d.items())

# ensure your BADGE_STYLE has your base look
BADGE_STYLE.update({"color": "#000", "fontStyle": "italic"})
BADGE_STYLE_CSS = dict_to_css(BADGE_STYLE) + "; color:#000 !important; font-style:italic !important;"

# Callback 2: Update the list of pdfs to be shown on the pdf file viewer section. Update it whenever the filters are clicked.
@app.callback(
    [
        Output('explorer-pdf-list-container', 'children'),
        Output('filtered-reports-store', 'data'),  # Add this output to store filtered reports
        Output('facility-dropdown', 'options'),
        Output('industry-dropdown', 'options'),
        Output('author-dropdown', 'options'),
        Output('base-material-dropdown', 'options'),
        Output('customer-dropdown', 'options'),
        Output('detailed-material-dropdown', 'options'),
        Output('sample-dropdown', 'options'),
        Output('condition-dropdown', 'options'),
        Output('spec-dropdown', 'options'),
        Output('testing-dropdown', 'options'), 
        Output('failure-dropdown', 'options'),
        Output('failure-env-dropdown', 'options'),
        Output('report-count','children'),
    ],
    [
        Input('year-slider', 'value'),
        Input('industry-dropdown', 'value'),
        Input('base-material-dropdown', 'value'),
        Input('author-dropdown', 'value'),
        Input('customer-dropdown', 'value'),
        Input('detailed-material-dropdown', 'value'),
        Input('sample-dropdown', 'value'),
        Input('condition-dropdown', 'value'),
        Input('spec-dropdown', 'value'),
        Input('testing-dropdown', 'value'), 
        Input('facility-dropdown', 'value'),
        Input('failure-dropdown', 'value'),
        Input('failure-env-dropdown', 'value')  
    ]
)
def update_pdf_list(year_range, selected_industries, selected_base_material, author, customer,
                    detailed_material, sample, condition, spec, testing, facility, failure_mode, failure_env):
    
    start_year, end_year = year_range
    
    logger.info("HERE WE ARE")
    ###### FIND THE PDFS AND MAKE TABLE
    params = {
        'facility': facility,
        'industry': selected_industries,
        'base_material': selected_base_material,
        'authors': author,
        'customers': customer,
        'detailed_materials': detailed_material,
        'samples': sample,
        'conditions': condition,
        'specs': spec,
        'testings': testing,
        'failure_mode': failure_mode, 
        'failure_env': failure_env,
        'start_date': f"{start_year}-01-01",
        'end_date' : f"{end_year}-12-31"
    }
    
    logger.info(params)
    
    df_filtered = executor.query_to_df(PDF_LIST_SQL(params))
    df_filtered.columns = df_filtered.columns.str.lower()
    
    filtered_reports = [f"/reports{file}" for file in df_filtered["file_val"].dropna().unique().tolist()]


    def to_display(row):
         # Extract and format the date (assuming the column is named 'creation_date')
        if 'creation_date' in row and pd.notnull(row['creation_date']):
            # Convert to datetime if not already
            creation_date = pd.to_datetime(row['creation_date'])
            formatted_date = creation_date.strftime("%Y")  # Format as "Year"
        else:
            formatted_date = "Unknown Date"  # Fallback if date is missing

        return (
# title on line 1, badges on line 2
                f"<div class='doc-wrap' style='color:#000 !important;'>"
                f"  <div class='doc-title' style='color:#000 !important;'>{row['report_name']}</div>"
                f"  <div class='tags'>"
                f"    <span class='badge' style='{BADGE_STYLE_CSS}'>{row['report_num']}</span>"
                f"    <span class='badge' style='{BADGE_STYLE_CSS}'>{formatted_date}</span>"
                f"    <span class='badge' style='{BADGE_STYLE_CSS}'>{row['basematerial_val']}</span>"
                f"    <span class='badge' style='{BADGE_STYLE_CSS}'>{row['industry_val']}</span>"
                f"  </div>"
                f"</div>"
    )

    
    records = df_filtered.assign(DOC=df_filtered.apply(to_display, axis=1)).to_dict("records")

    table = dash_table.DataTable(
        id="pdf-table",
        columns=[
            {"name": "", "id": "DOC", "presentation": "markdown"},
        ],
        data=records,
        page_action="none",
        virtualization=True,                    # keeps it fast with 1k rows
        fixed_rows={"headers": False},
        markdown_options={"html": True},        # allow our <span> badges
        style_table={"height": "75vh", "overflowY": "auto", "overflowX": "hidden", "width": "100%"},
        # 1) Inline styles (high priority) \97 make ALL cells black by default
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "lineHeight": "1.4rem",
            "padding": "10px",
            "color": "#333",
            "maxWidth": "0",  # This forces the cell to respect the container width
            "overflow": "hidden",
            "textOverflow": "ellipsis",

        },
         style_data_conditional=[
        {
            "if": {"state": "selected"},
            "backgroundColor": "#EBF5FB",  
            "border": f"1px solid {ELEMENT_BLUE}",
            "color": "#333",
        }
    ],
    css=[
        {"selector": ".dash-header", "rule": "display: none !important;"},
        # Force the viewport taller
        {"selector": "#explorer-pdf-list-container .dash-spreadsheet-container, "
                    "#explorer-pdf-list-container .dash-spreadsheet",
                     "rule": "height:calc(75vh - 30px) !important; max-height:none !important;"},        # Add hover effect
        {"selector": ".dash-spreadsheet-container .dash-spreadsheet-inner td:hover",
        "rule": "background-color: #f8f9fa !important; cursor: pointer !important;"}
    ],
    )
    
    ###### GET THE REST OF THE VARIABLES IN THE DROPDOWN

    def get_dict(col_name):
        opts = df_filtered[[col_name]].dropna().drop_duplicates().rename(columns={col_name:"value"})

        opts['label'] = opts['value']
        opts = opts.to_dict(orient="records")
        return sorted(opts, key=lambda x: x["label"].lower())
    
    # Dont enfore consistency on these 'privileged' filters:
    #facility_opts = get_dict("facility")
    #industry_opts = get_dict("industry_val")
    #author_opts = get_dict("author")
    customer_opts = get_dict("customer_name")
    detailed_material_opts = get_dict("detailed_material")
    sample_opts = get_dict("sample_type")
    condition_opts = get_dict("condition")
    specs_opts = get_dict("specs")
    testing_opts = get_dict("testing")
    failure_opts = get_dict("failure_mode")
    failure_env_opts = get_dict("failure_env")
    base_material_opts = get_dict("basematerial_val")
    
    num_reports = f"Showing {str(len(filtered_reports))} reports"
    
    return (
        ## table
        html.Div(table,id="pdf-table-wrap"), 
        filtered_reports, # Return the list of filtered reports
        ## filters, no_update for privileged filters
        no_update, # facility_opts, 
        no_update, # industry_opts,
        no_update, # author_opts,
        base_material_opts, 
        customer_opts, 
        detailed_material_opts, 
        sample_opts, 
        condition_opts, 
        specs_opts,
        testing_opts, 
        failure_opts, 
        failure_env_opts, 
        num_reports
    )

# ---------- APP LAYOUT CODE ---------------------

def create_navbar():
    """
    Creates a Bootstrap navbar component with Element branding
    """
    return dbc.Navbar(
        dbc.Container([
            # Branding section with logo and name
            html.A(
                dbc.Row([
                    dbc.Col(dbc.NavbarBrand("Element Materials Technology"),  
                           width="auto"),
                ],
                align="center",
                className="g-0"),
                href="/",
                style={"textDecoration": "none"},
            ),            
        ],
        fluid=True,
        style={"justifyContent": "start"}),  # Align content to the left
        color=ELEMENT_BLUE,
        dark=True,
        className="mb-4",
    )

app.layout = html.Div([
    dcc.Store(id="body-shift-trigger"),
    create_navbar(), # <- This is the blue bar at the top
    explorer_layout, # <- This is the document explorer layout
    chat_panel,      # <- This is the chatbot panel
])

app.validation_layout = html.Div([
    create_navbar(),
    # your actual layout pieces
    explorer_layout,
    chat_panel,
    # ---- DYNAMIC PLACEHOLDERS (not visible) ----
    # DataTable is created later by a callback; give Dash a stub now:
    dash_table.DataTable(id="pdf-table"),
    # Stores / components referenced by callbacks:
    dcc.Store(id='pdf-store'),
    html.Div(id='explorer-pdf-list-container'),
    # Offcanvas controls
    dbc.Button(id="open-chat"),
    dbc.Button(id="close-chat"),
    # Anything else you reference in callbacks that might be dynamic...
])