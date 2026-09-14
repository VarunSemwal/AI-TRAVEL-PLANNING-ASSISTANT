import streamlit as st

from travel_assistant.assistant import TravelAssistant
from travel_assistant.config import get_settings


@st.cache_resource
def get_assistant() -> TravelAssistant:
    return TravelAssistant(get_settings())


st.set_page_config(page_title="Singapore Travel Assistant")
st.title("Singapore Travel Assistant")
st.caption("Grounded destination knowledge with current weather and currency tools")

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("Reset conversation"):
    st.session_state.messages = []
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about Singapore attractions, weather, currency, or itineraries")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            response = get_assistant().answer(question, st.session_state.messages)
            st.markdown(response.answer)
            if response.citations:
                st.markdown("**Sources**")
                for citation in response.citations:
                    st.markdown(f"- [{citation.title}]({citation.url})")
            if response.tools_used:
                st.caption("Tools used: " + ", ".join(response.tools_used))
        except Exception as error:
            response_text = f"The assistant could not complete the request: {error}"
            st.error(response_text)
        else:
            response_text = response.answer
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )