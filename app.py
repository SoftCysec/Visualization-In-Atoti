from flask import Flask, request, render_template, redirect, session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import atoti as tt
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

# Set up Google OAuth2 client
client_secrets_file = "client_secret_18630754994-jijfr36066o1p0tkriahck3548u2mtct.apps.googleusercontent.com.json"
flow = Flow.from_client_secrets_file(
    client_secrets_file,
    scopes=["https://www.googleapis.com/auth/drive"],
    redirect_uri="https://localhost:5000/oauth2callback",
)


@app.route("/")
def index():
    if "credentials" in session:
        return redirect("/dashboard")
    else:
        auth_url, _ = flow.authorization_url(prompt="consent")
        return render_template("upload.html", auth_url=auth_url)


@app.route("/oauth2callback")
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)
    return redirect("/dashboard")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "credentials" not in session:
        return redirect("/")
    credentials = Credentials.from_authorized_user_info(session["credentials"])
    service = build("drive", "v3", credentials=credentials)
    files = service.files().list(q="mimeType='application/vnd.ms-excel' and trashed = false",
                                  fields="files(id, name)").execute().get("files", [])
    if request.method == "POST":
        file_id = request.form.get("file_id")
        file_name = request.form.get("file_name")
        df = read_excel_from_drive(file_id, credentials)
        session = tt.create_session(config={"user_content_storage": "memory"})
        table = session.read_pandas(df)

        # Get columns for hierarchies and measures
        hierarchy_cols = []
        measure_cols = []
        for col in df.columns:
            if col.lower() in ["category", "subcategory", "product"]:
                hierarchy_cols.append(col)
            else:
                measure_cols.append(col)

        # Create hierarchies
        hierarchies = {}
        for i in range(len(hierarchy_cols)):
            h_cols = hierarchy_cols[i:]
            h_name = "Hierarchy" + str(i+1)
            hierarchies[h_name] = h_cols

        # Create measures
        measures = {}
        for col in measure_cols:
            measures[col] = tt.agg.sum(table[col])

        # Create storage
        store = tt.create_store("h2")

        # Create cube
        cube = session.create_cube(table, "MyCube", store=store, hierarchy=hierarchies, measures=measures)

        # Create Atoti dashboard
        dashboard = cube.dashboard(title="My Dashboard")
        display(dashboard.export())
        return ""
    return render_template("dashboard.html", files=files)


def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "redirect_uris": ["http://localhost:5000/oauth2callback"]
    }



def read_excel_from_drive(file_id, credentials):
    service = build("drive", "v3", credentials=credentials)
    file = service.files().get(fileId=file_id).execute()
    file_name = file["name"]
    url = file["webViewLink"]

    # Download file content as Excel
    download_url = file["exportLinks"]["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    resp, content = service._http.request(download_url)
    
    # Load Excel file into pandas dataframe
    df = pd.read_excel(content, sheet_name=0)
    df["source_url"] = url
    df["source_file_name"] = file_name
    
    return df


if __name__ == '__main__':
    app.run(debug=True)
