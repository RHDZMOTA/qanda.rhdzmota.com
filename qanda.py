import uuid
import datetime as dt
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st

from rhdzmota.ext.streamlit_webapps.page_view import (
    PageView,
    PageViewHeader,
)


@dataclass(frozen=True, slots=True)
class Message:
    text: str
    from_session: Optional[str] = None
    from_thread: Optional[str] = field(default_factory=lambda: "main")
    from_author: Optional[str] = field(default_factory=lambda: "Unknown")
    created_at: str = field(default_factory=dt.datetime.utcnow)
    timestamp_formatting: str = field(default_factory=lambda: "%Y-%m-%d %H:%M:%S")
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_thread_key(self) -> str:
        return f"{self.from_session}:{self.from_thread}"

    @property
    def timestamp(self) -> str:
        return self.created_at.strftime(self.timestamp_formatting)

    def display_content(self, raw: bool = False):
        if raw:
            # Early exit if display content as 'raw'
            return st.text(self.text)
        # Wrap the message as a quote & display via markdown
        msg_text_with_fmt = "> " + self.text.replace("\n", "\n> ") 
        return st.markdown(msg_text_with_fmt)
    
    def display_thread(self):
        thread_key = f"{self.from_session}:{self.uuid}"
        if not thread_key in st.session_state:
            st.session_state[thread_key] = deque([])
        with st.expander("Replies :thread:"):
            for msg in st.session_state.get(thread_key):
                msg.display()
            with st.form(f"thread-{self.uuid}"):
                reply = st.text_input(label="Reply to message:")
                include_main_thread = st.checkbox(label="Send also in main thread")
                submitted = st.form_submit_button("Submit")
            if not submitted:
                return
            if not reply:
                return
            st.session_state[thread_key].append(
                Message(
                    text=reply,
                    from_session=self.from_session,
                    from_thread=self.uuid,
                )
            )
            st.rerun()

    def display_head(self):
        st.divider()
        level = "###" if self.from_thread == "main" else "####"
        st.markdown(f"{level} [{self.timestamp}] _{self.from_author}_:")
    
    def display(self, raw: bool = False):
        self.display_head()
        with st.container():
            self.display_content(raw=raw)
            if self.from_thread == "main":
                self.display_thread()

class Header(PageViewHeader):

    def on_start(self):
        st.markdown("# Session Q&A")
        # Extract configs from the page url-params

        # Setup the session keys
        session_key = "demo"
        st.session_state["session_key"] = "demo"
        # Main message thread
        main_thread_key = f"{session_key}:main"
        if main_thread_key not in st.session_state:
            system_message = Message(
                text="Hello! Welcome everyone.",
                from_session=session_key,
                from_thread="main",
                from_author="SYSTEM",
            )
            st.session_state[main_thread_key] = deque([system_message])


class QandaView(PageView, Header):
    def view(self, **kwargs):
        session_key = st.session_state["session_key"]
        main_thread_key = f"{session_key}:main"
        with st.container(height=600):
            st.markdown("## Live Comments")
            for msg in st.session_state[main_thread_key]:
                msg.display(raw=False)
            st.divider()

        with st.form(f"form-{self.refname}", clear_on_submit=True):
            message = st.text_area(label="Comment:")
            submitted = st.form_submit_button("Submit")

        if not submitted:
            return
        if not message:
            return
        st.session_state[main_thread_key].appendleft(
            Message(
                text=message,
                from_session=session_key,
                from_thread="main",
            )
        )
        st.rerun()


if __name__ == "__main__":
    with QandaView(page_title="Q&A", page_layout="wide") as page:
        page.view()
