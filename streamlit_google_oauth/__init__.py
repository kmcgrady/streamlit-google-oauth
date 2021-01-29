import os
import requests
import time
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
# (This is, of course, optional - there are innumerable ways to manage your
# release process.)
_RELEASE = False

# Declare a Streamlit component. `declare_component` returns a function
# that is used to create instances of the component. We're naming this
# function "_component_func", with an underscore prefix, because we don't want
# to expose it directly to users. Instead, we will create a custom wrapper
# function, below, that will serve as our component's public API.

# It's worth noting that this call to `declare_component` is the
# *only thing* you need to do to create the binding between Streamlit and
# your component frontend. Everything else we do in this file is simply a
# best practice.

if not _RELEASE:
    _component_func = components.declare_component(
        # We give the component a simple, descriptive name ("my_component"
        # does not fit this bill, so please choose something better for your
        # own component :)
        "st_google_oauth",
        # Pass `url` here to tell Streamlit that the component will be served
        # by the local dev server that you run via `npm run start`.
        # (This is useful while your component is in development.)
        url="https://5e31c462455e.ngrok.io",
    )
else:
    # When we're distributing a production version of the component, we'll
    # replace the `url` param with `path`, and point it to to the component's
    # build directory:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_google_oauth", path=build_dir)

class GoogleCredentials:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
        self._refresh_token = None
        self._last_refreshed = None
        self._expires_in = None
    
    def create_tokens(self, code, redirect_uri):
        print("Creating Tokens")
        r = requests.post("https://oauth2.googleapis.com/token", data={
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': "authorization_code"
        })
        json = r.json()

        if 'access_token' in json and 'refresh_token' in json and 'expires_in' in json:
            self._last_refreshed = time.time()
            self._access_token = json['access_token']
            self._refresh_token = json['refresh_token']
            self._expires_in = json['expires_in'] - 120
    
    def get_access_token(self):
        if self._access_token is None:
            return None

        if time.time() - self._last_refreshed >= self._expires_in:
            r = requests.post("https://oauth2.googleapis.com/token", data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self._refresh_token,
                'grant_type': "refresh_token"
            })
            json = r.json()

            if 'access_token' in json and 'refresh_token' in json and 'expires_in' in json:
                self._last_refreshed = time.time()
                self._access_token = json['access_token']
                self._refresh_token = json['refresh_token']
                self._expire_time = json['expires_in'] - 120

        return self._access_token


# Create a wrapper function for the component. This is an optional
# best practice - we could simply expose the component function returned by
# `declare_component` and call it done. The wrapper allows us to customize
# our component's API: we can pre-process its input args, post-process its
# output value, and add a docstring for users.
def st_google_oauth(credentials, scopes=[], key=None):
    """Create a new instance of "my_component".

    Parameters
    ----------
    name: str
        The name of the thing we're saying hello to. The component will display
        the text "Hello, {name}!"
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.

    Returns
    -------
    int
        The number of times the component's "Click Me" button has been clicked.
        (This is the value passed to `Streamlit.setComponentValue` on the
        frontend.)

    """
    token = credentials.get_access_token()
    if token is not None:
        print("No Need to rerun, just return the token")
        return token

    opts = _component_func(client_id=credentials.client_id, client_secret=credentials.client_secret, scopes=scopes, key=key, default=None)
    if opts is None:
        return None

    code, redirect_uri = opts
    credentials.create_tokens(code, redirect_uri)

    # We could modify the value returned from the component if we wanted.
    # There's no need to do this in our simple example - but it's an option.
    return credentials.get_access_token()


# Add some test code to play with the component while it's in development.
# During development, we can run this just as we would any other Streamlit
# app: `$ streamlit run my_component/__init__.py`
if not _RELEASE:
    import streamlit as st

    # We use the special "key" argument to assign a fixed identity to this
    # component instance. By default, when a component's arguments change,
    # it is considered a new instance and will be re-mounted on the frontend
    # and lose its current state. In this case, we want to vary the component's
    # "name" argument without having it get recreated.
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    SCOPES = [""]
    state = st.beta_session_state(credentials=GoogleCredentials(CLIENT_ID, CLIENT_SECRET))
    token = st_google_oauth(state.credentials, scopes=SCOPES, key="foo")

    if token is not None:
        import requests
        r = requests.get("https://www.googleapis.com/drive/v3/about?fields=user&access_token=" + token)
        json = r.json()
        st.json(json)
