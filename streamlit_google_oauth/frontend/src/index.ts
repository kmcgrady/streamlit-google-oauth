import { Streamlit, RenderData } from "streamlit-component-lib"

if (window.location.hash) {
  const fragmentString = window.location.hash.substring(1)
  const params: Record<string, string> = {}
  const regex = /([^&=]+)=([^&]*)/g
  let m
  while ((m = regex.exec(fragmentString))) {
    params[decodeURIComponent(m[1])] = decodeURIComponent(m[2])
  }
  if (Object.keys(params).length > 0) {
    localStorage.setItem("oauth2-params", JSON.stringify(params))
    window.opener.postMessage(params)
    window.close()
  }
}

function receiveMessage(event: MessageEvent) {
  if (event.origin !== window.location.origin) {
    return
  }

  const { data } = event
  if (data.state !== "streamlit-google-oauth") {
    return
  }

  Streamlit.setComponentValue(data)
}

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
function onRender(event: Event): void {
  document.body.innerHTML = ""
  // Get the RenderData from the event
  const data = (event as CustomEvent<RenderData>).detail
  const oauthParams = localStorage.getItem("oauth2-params")
  window.removeEventListener("message", receiveMessage)
  if (oauthParams) {
    const loggedInSpan = document.body.appendChild(
      document.createElement("span")
    )
    loggedInSpan.textContent = "Logged In!"
    return
  }

  const span = document.body.appendChild(document.createElement("span"))
  const button = span.appendChild(document.createElement("button"))

  button.textContent = "Login with Google!"
  button.addEventListener("click", () => {
    // Google's OAuth 2.0 endpoint for requesting an access token
    const oauth2Endpoint = new URL(
      "https://accounts.google.com/o/oauth2/v2/auth"
    )

    const params: Record<any, any> = {
      client_id: data.args.client_id,
      redirect_uri: window.location.href, // Redirect to itself.
      response_type: "token",
      scope: data.args.scopes.join(" "),
      include_granted_scopes: "true",
      state: "streamlit-google-oauth",
    }

    for (let p in params) {
      oauth2Endpoint.searchParams.append(p, params[p])
    }

    window.addEventListener("message", (event) => receiveMessage(event), false)

    const newWindow = window.open(
      oauth2Endpoint.toString(),
      "name",
      "height=600,width=450"
    )
    if (newWindow) {
      newWindow.focus()
    }
  })

  // We tell Streamlit to update our frameHeight after each render event, in
  // case it has changed. (This isn't strictly necessary for the example
  // because our height stays fixed, but this is a low-cost function, so
  // there's no harm in doing it redundantly.)
  Streamlit.setFrameHeight(200)
}

// Attach our `onRender` handler to Streamlit's render event.
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)

// Tell Streamlit we're ready to start receiving data. We won't get our
// first RENDER_EVENT until we call this function.
Streamlit.setComponentReady()

// Finally, tell Streamlit to update our initial height. We omit the
// `height` parameter here to have it default to our scrollHeight.
Streamlit.setFrameHeight(200)
